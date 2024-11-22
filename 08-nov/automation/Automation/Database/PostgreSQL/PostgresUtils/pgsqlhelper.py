# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Postgres related operations.

PostgresHelper, UnixObject and WindowsObject are 3 classes defined in this file.

PostgresHelper: Class for performing postgres related operation


PostgresHelper:
    __init__()                          -- initialise object of PostgresHelper object

    get_postgres_db_password()          -- Gets the db password of the instance

    strip_slash_char()                  -- strips the "/" character from database

    _get_postgres_database_connection() -- Gets the database connection object

    generate_table_size()               -- Generates the size of the table which is given as input

    get_tables_in_db()                  -- Get the list of tables available in the given
                                           Database Name

    get_schema_tables_in_db()           -- Gets the list of tables, schemas, sequences in a DB

    generate_db_info()                  -- Gets complete metadata info of Database

    validate_db_info()                  -- Takes two Database Information Maps and
                                            verifies if both have same info

    generate_test_data()                -- Function to generate test data for the
                                           automation purpose.
                                           Adds specified number of Databases, tables and
                                           rows with a specified Prefix

    insert_data_into_tables()           -- Inserts random strings to the table specified

    get_row_count()                     -- Gets the Number of rows in the table

    create_table()                      -- Creates a table of given name in the specified database

    drop_table()                        -- drops a table of given name in the specified database

    create_view()                       -- creates a view inside a database

    drop_view()                         -- drops a view inside a database

    list_views()                        -- lists views inside a database

    create_function()                   -- creates a function inside a database.

    drop_function()                     -- crops a function inside a database

    list_functions()                    -- lists all functions inside a database

    create_trigger()                    -- creates a trigger inside a database

    drop_trigger()                      -- drops a trigger inside a database.

    list_triggers()                     -- lists all triggers defined for the database server

    cleanup_tc_db()                     -- Clean Up test Databases of failed runs or
                                           completed TCs if exists

    cleanup_test_data()                 -- Cleans up test data which are generated for automation

    get_size_of_app_in_backup_phase()   -- Gets the size of application in backup phase

    start_postgres_server()             -- Starts the postgres server in client

    stop_postgres_server()              -- Stops the postgres server in client

    get_postgres_status()               -- Gets the postgres server status

    get_postgres_data_dir()             -- Gets the data directory of postgres server

    get_postgres_bin_dir()              -- Gets postgres binary directory

    check_chunk_commited()              -- Checks for chunk commit in the commserver for the
                                            initiated job

    get_subclient_database_list()       -- method to get databases associated with a given
    subclient in dumpbased backupset

    run_backup()                        -- initiates backup job from subclient level

    check_job_status()                  --  check job status and waits for completion

    get_metadata()                      -- fetches the postgres database information

    run_restore()                       -- initiates restore job from subclient level and
    waits for completion

    clone_backup_restore()              -- method to perform backup/restore and validation
    of clone feature TCs

    blocklevel_backup_restore()         -- method to perform backup/restore and validation
    of block level feature TCs

    set_port_and_listen_address()       -- method to set the clone port and the listen address
    in the postgresql.conf file in the cloned data directory

    cleanup_database_directories()      -- method to remove data and wal directory before
    fsbased restore

    get_replication_job()               -- method to fetch the replication job associated with
    live sync operation from commserv database

    check_postgres_recovery_mode()      -- checks if the postgres server is in recovery mode

    create_path_for_tablespace()        -- method to create tablespace directory

    is_backup_run_on_standby()          -- method to check if the backup is run on standby
    node or not

    get_standby_client_name()           -- gets the client name of the standby instance

    refresh()                           -- refresh DB connection

    get_wal_seg_size()                  -- To get the wal segment size from postgres server

    switch_log()                        -- To switch and create log for given number of times

    schedule_details()                  -- gets threshold values of automatic schedule

    get_afileid()                       -- Gets afileid for given job id, file type and flags

    confirm_logging()                   -- Confirm a pattern in commvault log for given job id
    and search term

    run_aux_copy()                      -- Perform aux copy for specified storage policy

    prepare_aux_copy()                  -- Complete requirements of storage policy copy for aux copy

    create_automatic_log_backup_schedule_policy --  method to create automatic log backup schedule policy

    get_postgres_db_obj()               -- Gets postgres database connection object

PostgresHelper instance Attributes
----------------------------------

    **postgres_port**                   --  returns the `postgres_port` of postgres server

    **postgres_db_user_name**           --  returns the `postgres db user name` of postgres server

    **postgres_server_url**             --  returns the `postgres server url` of postgres server

    **postgres_log_directory**          --  returns PostgresBackup.log path in the client

    **is_index_v2_postgres**            --  returns True if Postgres index version is V2

    **postgres_password**               --  returns postgres server password

    **is_pg_in_recovery**               -- checks if postgres server is in recovery

    **is_streaming_replication**        -- checks if postgres server is in streaming replication


PostgresClusterHelper:

    __init__(commcell, client, instance)        -- Initializes an object of the class with specified commcell, client and instance.

    get_node_priority()                         -- Returns the priority order of PostgreSQL clusters in the form of a Python dictionary.

    get_master_node()                           -- Fetches the client name of master node of the PostgreSQL cluster based on priority.

    get_node_data()                             -- Retrieves configuration data for all nodes in the PostgreSQL cluster.

    is_data_backup_on_standby(job_id)           -- Checks if a data backup was performed on the highest priority standby node for a given job ID.

    is_log_backup_on(node, job_id)              -- Checks if a log backup was performed on the master/priority node node for a given job ID.

    validate_log_delete(cluster_node)           -- Validates if wal files have been successfully deleted on a specified cluster node.

    update_conf_file(attribute_name, value)     -- Updates the PostgreSQL configuration file with a specified attribute name and value.
"""

import time
import re
from Application.CloudApps.azure_helper import AzureAuthToken
from AutomationUtils import logger
from AutomationUtils import constants
from AutomationUtils import idautils
from AutomationUtils import database_helper
from AutomationUtils import cvhelper
from AutomationUtils import machine
from Database.dbhelper import DbHelper


class PostgresHelper(object):
    """Helper class to perform Postgres operations"""

    def __init__(self, commcell, client=None, instance=None, connection_info=None, ssl_ca=None, is_mi=False,
                 backup_gateway=None):
        """Initialize the PostgresHelper object.

            Args:
                commcell             (obj)  --  Commcell object

                client               (obj)  --  Client object

                    default: None

                instance             (obj)  --  Postgres instance object

                    default: None

                connection_info      (dict) --  dictoinary containing connection information
                that needs to be provided only if client and instance objects are not provided

                    default: None

                    Format:
                        connection_info = {
                            'client_name': 'client_name',
                            'instance_name':'instance_name',
                            'port': 5432,
                            'hostname': 'hostname',
                            'user_name':'postgres',
                            'password': password,
                            'bin_directory':bin_directory (optional)}

                ssl_ca              (str) -- SSL CA path Location on the access node

                is_mi                  (bool) -- True , if managed identity based authentication

                backup_gateway      (str) -- backup_gateway name

            Returns:
                object - instance of this class

        """
        self._commcell = commcell
        self._csdb = database_helper.get_csdb()
        self._is_cloud_db = False
        self._pgsql_db_object = None
        self._pgsql_custom_db_object = None
        self._postgres_db_password = None
        self._total_tables = 500
        self._total_rows = 500
        self._table_number = 1
        self._connection = None
        self._cursor = None
        self._postgres_bin_directory = None
        self._db_connect = None
        self._postgres_instance = None
        self._ssl_enabled = None
        self._ssl_ca = ssl_ca
        self._ssl_cert = None
        self._ssl_key = None
        self._ad_auth_mi = is_mi
        self.backup_gateway = backup_gateway

        self.log = logger.get_log()
        self.ignore_db_list = ["postgres", "template0", "template1", "azure_maintenance", "azure_sys", "rdsadmin",
                               "cloudsqladmin"]
        if client and instance:
            self._client = client
            self._instance = instance
            self._postgres_client = instance._agent_object._client_object.client_name
            self._postgres_instance = instance
            self._postgres_port = self._instance.postgres_server_port_number
            self._postgres_server_url = self._client.client_hostname
            if str(self._postgres_port).find(":") >= 0:
                self._is_cloud_db = True
                self._postgres_port = self._instance.postgres_server_port_number.split(":")[1]
                self._postgres_server_url = self._instance.postgres_server_port_number.split(":")[0]
            self._postgres_db_user_name = self._instance.postgres_server_user_name
            self._postgres_bin_directory = self.get_postgres_bin_dir(
                self._client.client_name,
                self._instance.instance_name)

            self._ssl_enabled = self._instance.postgres_ssl_status
            if self._ssl_enabled:
                if not self._ssl_ca and self._instance.postgres_ssl_ca_file:
                    self._ssl_ca = self._instance.postgres_ssl_ca_file
                if self._instance.postgres_ssl_key_file:
                    self._ssl_cert = self._instance.postgres_ssl_key_file
                if self._instance.postgres_ssl_cert_file:
                    self._ssl_cert = self._instance.postgres_ssl_cert_file

            self.get_postgres_db_password()
            if self._client.os_info.find("Any") < 0:
                self.machine_object = machine.Machine(
                    self._client, self._commcell)
        elif connection_info:
            self._postgres_client = connection_info['client_name']
            self._postgres_port = connection_info['port']
            self._postgres_server_url = connection_info['hostname']
            self._postgres_db_user_name = connection_info['user_name']
            self._postgres_db_password = connection_info['password']
            self._postgres_instance_name = connection_info['instance_name']
            if not self._postgres_db_password:
                self.get_postgres_db_password()
            if connection_info['bin_directory']:
                self._postgres_bin_directory = connection_info['bin_directory']
            else:
                self._postgres_bin_directory = self.get_postgres_bin_dir(
                    self._postgres_client,
                    self._postgres_instance_name)
            self.machine_object = machine.Machine(connection_info['client_name'], self._commcell)
            self.connection_info = connection_info
        else:
            raise Exception(
                "Either client & instance objects or connection_info is required for class initialization")

    @property
    def postgres_port(self):
        """ getter for the postgres port """
        return self._postgres_port

    @postgres_port.setter
    def postgres_port(self, value):
        """ Setter for the postgres port """
        self._postgres_port = str(value)

    @property
    def pgsql_db_object(self):
        """ getter for the postgres db object """
        return self._pgsql_db_object

    @pgsql_db_object.setter
    def pgsql_db_object(self, value):
        """ Setter for the postgres db object """
        self._pgsql_db_object = value

    @property
    def postgres_db_user_name(self):
        """ getter for the postgres db username """
        return self._postgres_db_user_name

    @property
    def postgres_server_url(self):
        """ getter for the postgres server URL """
        return self._postgres_server_url

    @property
    def is_cloud_db(self):
        """ getter for the postgres server URL """
        return self._is_cloud_db

    @property
    def postgres_password(self):
        """Returns postgres server password"""
        return self._postgres_db_password

    def get_postgres_db_password(self):
        """Gets the db password of the instance

                Raises:
                    Exception:
                        if failed to get the db password of the instance """
        if self._postgres_instance:
            query = "Select attrVal from APP_InstanceProp where componentNameId = {0} and \
                            attrName ='PostgreSQL Use client cloud credentials'".format(
                self._postgres_instance.instance_id)
            self._csdb.execute(query)
            flag = self._csdb.fetch_one_row()
            ad_auth = flag[0]
            if len(ad_auth) != 0 and int(ad_auth) == 1:
                azure_pgsql_app_token_object = AzureAuthToken()
                if self._ad_auth_mi:
                    pgsql_db_password = azure_pgsql_app_token_object.generate_auth_token_mi_ad_auth(self.backup_gateway,
                                                                                                    self._commcell)
                    self._postgres_db_password = pgsql_db_password
                    return
                else:
                    pgsql_db_password = azure_pgsql_app_token_object.generate_auth_token_iam_ad_auth()
                    self._postgres_db_password = pgsql_db_password
                    return
            else:
                query = (
                    "Select attrVal from app_instanceprop where componentNameId = {0} and "
                    "attrName = 'PostgreSQL SA password'".format(
                        str(
                            self._postgres_instance.instance_id)))
        else:
            query = (
                "Select attrVal from app_instanceprop where componentNameId = "
                "(select distinct instance from APP_Application where instance in "
                "(select id from APP_InstanceName where name='{1}') and clientId="
                "(select id from app_client where name='{0}')) and "
                "attrName = 'PostgreSQL SA password'".format(
                    self._postgres_client, self._postgres_instance_name))
        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()

        if cur:
            self._postgres_db_password = cvhelper.format_string(
                self._commcell, cur[0])
            self.log.info("Password for postgres db is fetched Successfully")
        else:
            raise Exception("Failed to get the postgres database password")

    @classmethod
    def strip_slash_char(cls, db_list):
        """
        strips the "/" character from database

        When we fetch subclient content from CSDB, the
        database names are prefixed with "/" character
        hence we use this fucntion to strip that from db name


        Args:
            db_list     (list)  --  Database List fetched from csdb
                                        having / character as prefix

            Returns:
                list - Db List without "/"

        """
        db_list_new = []
        for i in db_list:
            db_list_new.append(i.strip("/"))
        return db_list_new

    def _get_postgres_database_connection(self, hostname, port, user_name, password, database):
        """
        Get the postgres database connection

        Args:
                hostname    (Str)  --  Hostname of client

                port        (str)  -- Port number of postgres server

                user_name   (str)  -- Username of postgres server

                password    (str)  -- Password of postgres server

                database    (str)  -- Database name

            Returns:
                Postgres database connection object
        """

        if database != 'postgres':
            if self._pgsql_custom_db_object is None or self._pgsql_custom_db_object.database != database:
                postgres_database_object = database_helper.PostgreSQL(
                    hostname, port, user_name, password, database,
                    ssl=self._ssl_enabled, ssl_ca=self._ssl_ca, ssl_cert=self._ssl_cert, ssl_key=self._ssl_key)
                self._pgsql_custom_db_object = postgres_database_object
            else:
                postgres_database_object = self._pgsql_custom_db_object
        else:
            if self.pgsql_db_object is None:
                postgres_database_object = database_helper.PostgreSQL(
                    hostname, port, user_name, password, database,
                    ssl=self._ssl_enabled, ssl_ca=self._ssl_ca, ssl_cert=self._ssl_cert, ssl_key=self._ssl_key)
                self.pgsql_db_object = postgres_database_object
            else:
                postgres_database_object = self.pgsql_db_object

        return postgres_database_object

    def generate_table_size(
            self,
            database,
            hostname,
            port,
            user_name,
            password,
            table_name=None):
        """ Generates the size of the table which is given as input
            Args:

                database    (str)  -- Database name

                hostname    (Str)  --  Hostname of client

                port        (str)  -- Port number of postgres server

                user_name   (str)  -- Username of postgres server

                password    (str)  -- Password of postgres server

                table_name  (str)  -- Table name


            Returns:
                List - (Table name, size)

            Raises:
                Exception:
                if unable generate table size

        """
        try:
            postgres_database_object = self._get_postgres_database_connection(
                hostname, port, user_name, password, database)
            # Get the list of the tables for the database
            tables = None
            tables_meta = None
            db_meta = []
            if table_name is None:
                self.log.info("Getting tables information for %s Database", database)
                tables, tables_meta = self.get_schema_tables_in_db(
                    database, hostname, port, user_name, password)
            else:
                tables = []
                tables.append(table_name)

            rowlist = []
            for each_row in tables_meta:

                split_tables_meta = each_row.split('.')
                schema_name = split_tables_meta[0]
                table_name = split_tables_meta[1]
                is_table = split_tables_meta[2]

                if is_table == 'TABLE':
                    query_set_search_path = "SET SEARCH_PATH=\"%s\";" % schema_name
                    postgres_database_object.execute(query_set_search_path)

                    query = "select count(*) from \"%s\"" % table_name
                    postgres_response = postgres_database_object.execute(query)
                    rowlist.append(postgres_response.rows[0])

            tab_row = list(zip(tables, rowlist))
            view_list = sorted(self.list_views(postgres_database_object))
            function_list = sorted(self.list_functions(postgres_database_object))
            trigger_list = sorted(self.list_triggers(postgres_database_object))
            db_meta = [tab_row, tables_meta, view_list, function_list, trigger_list]
            return db_meta

        except Exception as exp:
            raise Exception("Exception {0} in GenerateTableSize".format((str(exp))))

    def get_tables_in_db(
            self,
            database,
            hostname,
            port,
            user_name,
            password):
        """
        Get the list of tables available in the given Database Name

        Args:
                database    (str)  -- Database name

                hostname    (Str)  --  Hostname of client

                port        (str)  -- Port number of postgres server

                user_name   (str)  -- Username of postgres server

                password    (str)  -- Password of postgres server



            Returns:
                List - Tables in Dabatase

            Raises:
                Exception:
                if unable to get table in db

        """
        tables_list = list()
        try:
            # Check if database exists or not
            postgres_database_object = self._get_postgres_database_connection(
                hostname, port, user_name, password, database)

            postgres_database_object.check_if_db_exists(database)

            # Run the query to get the list of tables in the database
            query = ("select tablename FROM pg_catalog.pg_tables WHERE "
                     "tablename NOT LIKE 'pg\_%' and tablename NOT LIKE 'sql\_%'")
            postgres_response = postgres_database_object.execute(query)
            for row in postgres_response.rows:
                tables_list.append(row[0])
            return tables_list

        except Exception as exp:
            raise Exception("Exception {0} in get_tables_in_db".format(str(exp)))

    def get_schema_tables_in_db(
            self,
            database,
            hostname,
            port,
            user_name,
            password):
        """
        Get the list of tables, schemas, sequences and indxes available in the given Database Name

        Args:
                database    (str)  -- Database name

                hostname    (Str)  --  Hostname of client

                port        (str)  -- Port number of postgres server

                user_name   (str)  -- Username of postgres server

                password    (str)  -- Password of postgres server



            Returns:
                List - Tables in Dabatase, Metadata of Schema

            Raises:
                Exception:
                if unable to get table in db

        """
        tables_list = list()
        tables_list_meta = list()
        try:
            # Check if database exists or not
            postgres_database_object = self._get_postgres_database_connection(
                hostname, port, user_name, password, database)
            postgres_database_object.check_if_db_exists(database)

            # Run the query to get the list of tables in the database
            query = ("select nsp.nspname as schema_name,cls.relname as object_name, "
                     "rol.rolname as owner, case cls.relkind when 'r' then 'TABLE' when 'i' "
                     "then 'INDEX' when 'S' then 'SEQUENCE' when 'v' then 'VIEW' when 'c' "
                     "then 'TYPE' else cls.relkind::text end as object_type FROM pg_class "
                     "cls join pg_roles rol on rol.oid = cls.relowner join pg_namespace "
                     "nsp on nsp.oid = cls.relnamespace where nsp.nspname not in "
                     "('information_schema', 'pg_catalog') and nsp.nspname not like "
                     "'pg_toast%' order by nsp.nspname, cls.relname")
            postgres_response = postgres_database_object.execute(
                query)
            for row in postgres_response.rows:
                tables_list_meta.append(row[0] + "." + row[1] + "." + row[3])
                if row[3] == 'TABLE':
                    tables_list.append(row[1])
            return (tables_list, tables_list_meta)
        except Exception as exp:
            raise Exception("Exception {0} in get_schema_tables_in_db".format(str(exp)))

    def generate_db_info(
            self,
            db_list,
            hostname,
            port,
            user_name,
            password):
        """
        Gets complete metadata info of Database

        Args:
                db_list     (list) -- Database list

                hostname    (Str)  -- Hostname of client

                port        (str)  -- Port number of postgres server

                user_name   (str)  -- Username of postgres server

                password    (str)  -- Password of postgres server


        Returns:
            Dict - Database Meta data information

        Raises:
            Exception:
            if unable to generate db info

        """
        for database in self.ignore_db_list:
            if database in db_list:
                db_list.remove(database)
        db_info_dict = dict()
        try:
            for database in db_list:
                table_info_map = None
                table_info_map = self.generate_table_size(
                    database,
                    hostname,
                    port,
                    user_name,
                    password)
                db_info_dict[database] = table_info_map
                self.log.info(
                    "Information of all the tables present in the "
                    "database %s: %s ", database, db_info_dict)
            return dict(db_info_dict)
        except Exception as exp:
            raise Exception("Exception {0} in generate_db_info".format(str(exp)))

    def validate_db_info(self, db_info_map_1, db_info_map_2):
        """
        Takes two Database Information Maps and verifies if both have same info

        Args:
                db_info_map_1        (dict)  -- Database info of 1st database

                db_info_map_2        (dict)  -- Database info of 2nd database

        Returns:
            Boolean - Validation status(True/False)

        Raises:
            Exception:
                if information validation fails

                if unable to validate the db info

        """
        self.log.info("Validating the database information")
        validation_status = True
        try:
            for database in db_info_map_1.keys():
                # Check if database exists or not
                if database not in db_info_map_2.keys():
                    validation_status = False

                else:
                    # Check if tables exists or not
                    tables_info_in_first_map = db_info_map_1[database]
                    tables_info_in_second_map = db_info_map_2[database]
                    for table in tables_info_in_first_map:
                        if table not in tables_info_in_second_map:
                            validation_status = False
            if not validation_status:
                raise Exception(
                    "Database information validation FAILED.!!!")
            self.log.info(
                "###Database information validation PASSED..!!###")
            return validation_status
        except Exception as exp:
            raise Exception("Exception {0} in validate_db_info".format(str(exp)))

    def generate_test_data(
            self,
            hostname,
            num_of_databases,
            num_of_tables,
            num_of_rows,
            port,
            user_name,
            password,
            delete_if_already_exist,
            database_prefix,
            tablespace=None):
        """ Function to generate test data for the automation purpose. Adds specified number of
        Databases, tables and Rows with a specified Prefix

        Args:
            hostname                (Str)       --  Hostname of client

            num_of_databases        (str)       -- Number of database to create

            num_of_tables           (str)       -- Number of tables to create inside each db

            num_of_rows             (str)       -- Number of rows in each table

            port                    (str)       -- Port number of postgres server

            user_name               (str)       -- Username of postgres server

            password                (str)       -- Password of postgres server

            delete_if_already_exist (bool)      -- Drop db if already exists

            database_prefix         (str)       -- Prefix name for each db created

            tablespace              (str)       -- Tablespace to be used to create database

                    Default: None

        Returns:
            Returns List of Databases on success

        Raises:
            Exception:
            if unable to generate test data

        """
        test_db_list = []
        postgres_database_object = self._get_postgres_database_connection(
            hostname, port, user_name, password, "postgres")
        try:
            for i in range(0, int(num_of_databases), 1):
                database = "{0}_testdb_{1}".format(database_prefix, i)
                if i == (num_of_databases - 1) and i != 0:
                    database = "{0}_Testdb {1}".format(database_prefix, i)
                # Check if database exists or not
                if postgres_database_object.check_if_db_exists(database):
                    postgres_database_object.drop_db(
                        database)
                log_msg = ("Creating %s PGSQL database in %s host on %s port "
                           "with %s userName"
                           % (database, hostname, str(port), user_name))
                self.log.info(log_msg)
                if tablespace is None:
                    postgres_database_object.create_db(
                        database)
                else:
                    postgres_database_object.create_tablespace_db(
                        database,
                        tablespace)
                postgres_database_object = database_helper.PostgreSQL(
                    hostname, port, user_name, password, database,
                    ssl=self._ssl_enabled, ssl_ca=self._ssl_ca, ssl_cert=self._ssl_cert, ssl_key=self._ssl_key)
                self._pgsql_custom_db_object = postgres_database_object
                self.log.debug("connection created for new db")
                for j in range(0, int(num_of_tables), 1):
                    table_name = f"testtab_{j}"
                    if i == (num_of_databases - 1) and i != 0:
                        table_name = f"Testtab {j}"
                    self.create_table(
                        table_name,
                        hostname,
                        port,
                        user_name,
                        password,
                        database)
                    # Insert values in to the table
                    self.insert_data_into_tables(
                        table_name,
                        postgres_database_object,
                        num_of_rows)
                    self.log.info("Creating views, triggers and functions")
                    self.create_view(
                        "select count(*) from \"{0}\";".format(table_name),
                        "test_view_{0}".format(j),
                        postgres_database_object)
                    self.create_function(
                        "test_function_{0}".format(j),
                        table_name,
                        postgres_database_object)

                test_db_list.append(database)
            if int(num_of_tables) > 1:
                self.create_trigger(
                    "test_trigger_0",
                    "testtab_0",
                    "testtab_1",
                    database="{0}_testdb_0".format(database_prefix))
            return test_db_list

        except Exception as exp:
            raise Exception("Exception {0} in generate_test_data".format(str(exp)))

    def insert_data_into_tables(
            self,
            table_name,
            con,
            num_of_rows):
        """Inserts random strings to the table specified

        Args:
            table_name          (str)   -- Name of table

            con                 (obj)   -- PostgreSQL DB connection object

            num_of_rows         (str)   -- Number of rows in each table

        Raises:
            Exception:
            if unable to insert test data

        """
        try:
            postgres_database_object = con
            query = ("insert into \"%s\" "
                     "select 10,'test_data','bangalore' "
                     "from generate_series(1, %s) s(i)" % (table_name, num_of_rows))
            postgres_database_object.execute(query)

        except Exception as exp:
            raise Exception("Exception {0} in insert_data_into_tables".format(str(exp)))

    def get_row_count(
            self,
            table_name,
            hostname,
            port,
            user_name,
            password,
            database):
        """Gets the Number of rows in the table

        Args:
            table_name          (str)   -- Name of table

            hostname            (Str)   --  Hostname of client

            port                (str)   -- Port number of postgres server

            user_name           (str)   -- Username of postgres server

            password            (str)   -- Password of postgres server

            database            (str)   -- Database name


        Returns:
            Returns row count on success

        Raises:
            Exception:
            if unable to get row count

        """
        try:
            postgres_database_object = self._get_postgres_database_connection(
                hostname, port, user_name, password, database)
            postgres_database_object.check_if_db_exists(database)

            query = "select * from \"%s\"" % table_name
            postgres_response = postgres_database_object.execute(query)
            return postgres_response
        except Exception as exp:
            raise Exception("Exception {0} in get_row_count".format(str(exp)))

    def create_table(
            self,
            table_name,
            hostname,
            port,
            user_name,
            password,
            database):
        """Creates a table of given name in the specified database

        Args:
            table_name          (str)  -- Name of table

            hostname            (Str)  -- Hostname of client

            port                (str)  -- Port number of postgres server

            user_name           (str)  -- Username of postgres server

            password            (str)  -- Password of postgres server

            database            (str)  -- Database name

        Raises:
            Exception:
            if unable to create table

        """
        try:

            postgres_database_object = self._get_postgres_database_connection(
                hostname, port, user_name, password, database)
            postgres_database_object.check_if_db_exists(database)
            query = ("CREATE TABLE \"{0}\" ("
                     "id int,"
                     "name VARCHAR(10),"
                     "city VARCHAR(10)"
                     ");".format(table_name))
            postgres_database_object.execute(query)
            self.log.info("Created table: %s", table_name)
        except Exception as exp:
            raise Exception("Exception {0} in create_table".format(str(exp)))

    def drop_table(
            self,
            table_name,
            hostname,
            port,
            user_name,
            password,
            database):
        """Drops a table of given name in the specified database

        Args:
            table_name          (str)  -- Name of table

            hostname            (Str)  -- Hostname of client

            port                (str)  -- Port number of postgres server

            user_name           (str)  -- Username of postgres server

            password            (str)  -- Password of postgres server

            database            (str)  -- Database name

        Raises:
            Exception:

                if database doesn't exists

                if unable to drop table

        """
        try:
            postgres_database_object = self._get_postgres_database_connection(
                hostname, port, user_name, password, database)
            postgres_database_object.check_if_db_exists(database)
            if postgres_database_object.check_if_db_exists(database):
                query = "drop table if exists \"{0}\" cascade;".format(table_name)
                self.log.info("Dropping the table: %s", table_name)
                postgres_database_object.execute(query)
            else:
                self.log.error("Database doesn't exists")
        except Exception as exp:
            self.log.error("Exception {0} while dropping table".format(str(exp)))
            raise Exception("Unable to drop tables in db")

    def create_view(
            self,
            query,
            view_name,
            postgres_db=None,
            database=None):
        """ Creates a view inside a database.

            Args:
                query          (str)  -- Query to create view

                view_name      (str)  -- Name of the view

                postgres_db    (obj)  -- postgres database object

                    default: None

                database       (str)  -- database name

                    default: None

            Raises:
                Exception:
                    if unable to create view
        """
        try:
            if postgres_db is None:
                # Establish the connection with database
                postgres_db = database_helper.PostgreSQL(
                    self.postgres_server_url,
                    self.postgres_port,
                    self.postgres_db_user_name,
                    self.postgres_password,
                    database,
                    ssl=self._ssl_enabled,
                    ssl_ca=self._ssl_ca,
                    ssl_cert=self._ssl_cert,
                    ssl_key=self._ssl_key
                )
            query = "create view {0} as {1};".format(view_name, query)
            postgres_db.execute(query)

        except Exception as exp:
            self.log.error("Exception {0} in creating View".format(str(exp)))
            raise Exception("Unable to create the view")

    def drop_view(
            self,
            view_name,
            postgres_db=None,
            database=None):
        """ Drops a view inside a database.

            Args:
                view_name      (str)  -- Name of the view

                postgres_db    (obj)  -- postgres database object

                    default: None

                database       (str)  -- database name

                    default: None

            Raises:
                Exception:
                    if unable to drop view
        """
        try:
            if postgres_db is None:
                # Establish the connection with database
                postgres_db = database_helper.PostgreSQL(
                    self.postgres_server_url,
                    self.postgres_port,
                    self.postgres_db_user_name,
                    self.postgres_password,
                    database,
                    ssl=self._ssl_enabled,
                    ssl_ca=self._ssl_ca,
                    ssl_cert=self._ssl_cert,
                    ssl_key=self._ssl_key)
            query = "drop view if exists {0} cascade;".format(view_name)
            postgres_db.execute(query)

        except Exception as exp:
            self.log.error("Exception {0} in dropping View".format(str(exp)))
            raise Exception("Unable to drop the view")

    def list_views(
            self,
            postgres_db=None,
            database=None):
        """ Lists views inside a database.

            Args:
                postgres_db    (obj)  -- postgres database object

                    default: None

                database       (str)  -- database name

                    default: None

            Returns:

                view_list      (list) -- list of views in the database

            Raises:
                Exception:
                    if unable to list views
        """
        try:
            if postgres_db is None:
                # Establish the connection with database
                postgres_db = database_helper.PostgreSQL(
                    self.postgres_server_url,
                    self.postgres_port,
                    self.postgres_db_user_name,
                    self.postgres_password,
                    database,
                    ssl=self._ssl_enabled,
                    ssl_ca=self._ssl_ca,
                    ssl_cert=self._ssl_cert,
                    ssl_key=self._ssl_key)
            query = ("select viewname FROM pg_views WHERE schemaname "
                     "NOT IN('information_schema', 'pg_catalog');")
            response_object = postgres_db.execute(query)
            rows = response_object.rows
            view_list = []
            for view_name in rows:
                view_list.append(view_name[0].strip())
            return view_list

        except Exception as exp:
            self.log.error("Exception {0} in listing Views".format(str(exp)))
            raise Exception("Unable to list views")

    def create_function(
            self,
            function_name,
            table_name="tab1",
            postgres_db=None,
            database=None):
        """ Creates a function inside a database.

            Args:

                function_name  (str)  -- Name of the function

                table_name     (str)  -- Name of the table

                postgres_db    (obj)  -- postgres database object

                    default: None

                database       (str)  -- database name

                    default: None

            Raises:
                Exception:
                    if unable to create a function
        """
        try:
            if postgres_db is None:
                # Establish the connection with database
                postgres_db = database_helper.PostgreSQL(
                    self.postgres_server_url,
                    self.postgres_port,
                    self.postgres_db_user_name,
                    self.postgres_password,
                    database,
                    ssl=self._ssl_enabled,
                    ssl_ca=self._ssl_ca,
                    ssl_cert=self._ssl_cert,
                    ssl_key=self._ssl_key)
            query = ("create OR REPLACE FUNCTION  {0}(pcode integer) returns bigint "
                     "AS $BODY$ select count(*) from \"{1}\" where id=pcode; $BODY$ LANGUAGE "
                     "sql VOLATILE COST 100;").format(function_name, table_name)
            postgres_db.execute(query)

        except Exception as exp:
            self.log.error("Exception {0} in creating function".format(str(exp)))
            raise Exception("Unable to create the function")

    def drop_function(
            self,
            function_name,
            postgres_db=None,
            database=None):
        """ Drops a function inside a database.

            Args:

                function_name  (str)  -- Name of the function

                postgres_db    (obj)  -- postgres database object

                    default: None

                database       (str)  -- database name

                    default: None

            Raises:
                Exception:
                    if unable to drop function
        """
        try:
            if postgres_db is None:
                # Establish the connection with database
                postgres_db = database_helper.PostgreSQL(
                    self.postgres_server_url,
                    self.postgres_port,
                    self.postgres_db_user_name,
                    self.postgres_password,
                    database,
                    ssl=self._ssl_enabled,
                    ssl_ca=self._ssl_ca,
                    ssl_cert=self._ssl_cert,
                    ssl_key=self._ssl_key)
            query = "drop function if exists {0}(integer);".format(function_name)
            postgres_db.execute(query)

        except Exception as exp:
            self.log.error("Exception {0} in dropping function".format(str(exp)))
            raise Exception("Unable to drop the function")

    def list_functions(
            self,
            postgres_db=None,
            database=None):
        """ Lists all functions inside a database.

            Args:

                postgres_db         (obj)  -- postgres database object

                    default: None

                database            (str)  -- database name

                    default: None

            Returns:
                function_list       (list) -- list of functions

            Raises:
                Exception:
                    if unable to list the functions
        """
        try:
            if postgres_db is None:
                # Establish the connection with database
                postgres_db = database_helper.PostgreSQL(
                    self.postgres_server_url,
                    self.postgres_port,
                    self.postgres_db_user_name,
                    self.postgres_password,
                    database,
                    ssl=self._ssl_enabled,
                    ssl_ca=self._ssl_ca,
                    ssl_cert=self._ssl_cert,
                    ssl_key=self._ssl_key)
            query = ("select routine_name FROM information_schema.routines "
                     "WHERE routine_type='FUNCTION' AND specific_schema='public';")
            response_object = postgres_db.execute(query)
            rows = response_object.rows
            function_list = []
            for function_name in rows:
                function_list.append(function_name[0].strip())
            return function_list

        except Exception as exp:
            self.log.error("Exception {0} in listing trigger".format(str(exp)))
            raise Exception("Unable to list the triggers")

    def create_trigger(
            self,
            trigger_name,
            table_name,
            trigger_table_name,
            postgres_db=None,
            database=None):
        """ creates a trigger inside a database.

            Args:

                trigger_name        (str)  -- Name of the function

                table_name          (str)  -- Name of the table where data needs
                to be inserted after a trigger

                trigger_table_name  (str)  -- Name of the table on which is
                trigger is defined

                postgres_db         (obj)  -- postgres database object

                    default: None

                database            (str)  -- database name

                    default: None

            Raises:
                Exception:
                    if unable to create a trigger
        """
        try:
            if postgres_db is None:
                # Establish the connection with database
                postgres_db = database_helper.PostgreSQL(
                    self.postgres_server_url,
                    self.postgres_port,
                    self.postgres_db_user_name,
                    self.postgres_password,
                    database,
                    ssl=self._ssl_enabled,
                    ssl_ca=self._ssl_ca,
                    ssl_cert=self._ssl_cert,
                    ssl_key=self._ssl_key)
            query = ("create OR REPLACE FUNCTION exmp_func() RETURNS trigger AS $BODY$ BEGIN"
                     " insert into \"{0}\" values(1, 'test'); RETURN NEW; END; "
                     "$BODY$ LANGUAGE plpgsql").format(table_name)
            postgres_db.execute(query)
            self.log.info("Trigger function created")
            query = ("create TRIGGER {0} AFTER INSERT ON \"{1}\" FOR "
                     "EACH ROW EXECUTE PROCEDURE exmp_func();").format(
                trigger_name, trigger_table_name)
            postgres_db.execute(query)

        except Exception as exp:
            self.log.error("Exception {0} in creating trigger".format(str(exp)))
            raise Exception("Unable to create the trigger")

    def drop_trigger(
            self,
            trigger_name,
            postgres_db=None,
            database=None):
        """ Drops a trigger inside a database.

            Args:

                trigger_name        (str)  -- Name of the function

                postgres_db         (obj)  -- postgres database object

                    default: None

                database            (str)  -- database name

                    default: None

            Raises:
                Exception:
                    if unable to drop trigger
        """
        try:
            if postgres_db is None:
                # Establish the connection with database
                postgres_db = database_helper.PostgreSQL(
                    self.postgres_server_url,
                    self.postgres_port,
                    self.postgres_db_user_name,
                    self.postgres_password,
                    database,
                    ssl=self._ssl_enabled,
                    ssl_ca=self._ssl_ca,
                    ssl_cert=self._ssl_cert,
                    ssl_key=self._ssl_key)
            query = "DROP TRIGGER {0};".format(trigger_name)
            postgres_db.execute(query)
            self.drop_function("exmp_func", postgres_db)

        except Exception as exp:
            self.log.error("Exception {0} in dropping trigger".format(str(exp)))
            raise Exception("Unable to drop the trigger")

    def list_triggers(
            self,
            postgres_db=None,
            database=None):
        """ Lists all triggers defined for the database server.

            Args:

                postgres_db         (obj)  -- postgres database object

                    default: None

                database            (str)  -- database name

                    default: None

            Returns:
                trigger_list        (list) -- list of triggers

            Raises:
                Exception:
                    if unable to list the triggers
        """
        try:
            if postgres_db is None:
                # Establish the connection with database
                postgres_db = database_helper.PostgreSQL(
                    self.postgres_server_url,
                    self.postgres_port,
                    self.postgres_db_user_name,
                    self.postgres_password,
                    database,
                    ssl=self._ssl_enabled,
                    ssl_ca=self._ssl_ca,
                    ssl_cert=self._ssl_cert,
                    ssl_key=self._ssl_key)

            query = "select tgname FROM pg_trigger;"
            response_object = postgres_db.execute(query)
            rows = response_object.rows
            trigger_list = []
            for trigger_name in rows:
                trigger_list.append(trigger_name[0].strip())
            return trigger_list

        except Exception as exp:
            self.log.error("Exception {0} in listing trigger".format(str(exp)))
            raise Exception("Unable to list the triggers")

    def cleanup_tc_db(
            self,
            pgsql_server_hostname,
            pgsql_server_port,
            pgsql_server_user_name,
            pgsql_server_password,
            tc_name):
        """ Clean Up test Databases of failed runs or completed TCs if exists

        Args:

            pgsql_server_hostname    (Str)   --  Hostname of client

            pgsql_server_port        (str)   -- Port number of postgres server

            pgsql_server_user_name   (str)   -- Username of postgres server

            pgsql_server_password    (str)   -- Password of postgres server

            tc_name                  (str)   -- Table Name

        """
        all_db_list = None
        self.log.info("Cleaning up test data")
        postgres_database_object = self._get_postgres_database_connection(
            pgsql_server_hostname, pgsql_server_port, pgsql_server_user_name, pgsql_server_password, "postgres")
        all_db_list = postgres_database_object.get_db_list()
        if all_db_list is None:
            self.log.error("Unable to retrieve all Database Names in PostGres Server")
            raise Exception("Unable to get the db list.")
        dbs_to_delete = list()
        # Extract only test Cases related DB Names
        for database in all_db_list:
            if database.startswith(tc_name):
                dbs_to_delete.append(database)

        # Drop the database of subclient content
        if dbs_to_delete:
            self.cleanup_test_data(
                dbs_to_delete,
                postgres_database_object)

    def cleanup_test_data(
            self,
            db_list,
            postgres_database_object=None):
        """
        Cleans up test data which are generated for automation

        Args:

            db_list                  (str) -- Database list

            postgres_database_object (obj) -- PostgreSQL connection object

        Raises:
            Exception:
            if unable to cleanup databases

        """
        try:
            if postgres_database_object is None:
                postgres_database_object = self._get_postgres_database_connection(
                    self._postgres_server_url, self._postgres_port, self._postgres_db_user_name,
                    self._postgres_db_password, "postgres")
            self._pgsql_custom_db_object = None
            for database in db_list:
                if postgres_database_object.check_if_db_exists(
                        database):
                    self.log.info("Dropping the database: %s", database)
                    postgres_database_object.drop_db(
                        database)
        except Exception as exp:
            raise Exception("Exception {0} in cleanup_test_data".format(str(exp)))

    def get_size_of_app_in_backup_phase(self, job_id, phase=7):
        """Gets the size_of_application in backup phase of JOB

        Args:
            job_id   (str)   -- JOB ID

            phase    (int)   -- Phase Id

                default: 7

        Returns: Returns size of application in backup phase

        Raises:
            Exception:
                if failed to get the size of application in backup phase

        """
        if not isinstance(job_id, str):
            raise Exception("The JOB ID has to be string")
        query = ("select (((sum(unCompBytes))/1024)/1024) FROM "
                 "JMBkpAtmptStats where jobId='{0}' and phase={1};".format(
            job_id, phase))
        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()
        if cur:
            size_of_application = cur[0]
            self.log.info(
                "Fetched Size of application in backup phase:%s", size_of_application)
            return size_of_application
        else:
            raise Exception(
                "Failed to get the size of application in backup phase")

    def start_postgres_server(
            self,
            pgsql_bin_dir,
            pgsql_data_dir):
        """ Starts the postgres server in client
        Args:

            pgsql_bin_dir        (str)  -- postgres bin directory path

            pgsql_data_dir       (str)  -- postgres data directory path

        """
        return_code = self.get_postgres_status(
            pgsql_bin_dir, pgsql_data_dir)
        if not return_code:
            self.log.info("Postgres Server is not running, starting the server")
            data = {
                'BINDIR': pgsql_bin_dir,
                'DATADIR': pgsql_data_dir,
                'OPERATION': "start"
            }
            if "unix" in self.machine_object.os_info.lower():
                output = self.machine_object.execute_script(
                    constants.UNIX_POSTGRES_START_STOP,
                    data)
                self.log.debug(
                    "Output of Postgres server start script: %s", output.formatted_output)
            else:
                pgctl_path = self.machine_object.join_path(pgsql_bin_dir, "pg_ctl.exe")
                command = 'cmd /c "\"{0}\" -U postgres -D \"{1}\" -s start"'.format(
                    pgctl_path, pgsql_data_dir)
                self._client.execute_command(command, wait_for_completion=False)
            time.sleep(15)
            return_code = self.get_postgres_status(
                pgsql_bin_dir, pgsql_data_dir)
            if return_code:
                self.log.info("Successfully started the Postgres Server")
            else:
                raise Exception("Unable to Start Postgres server, Error while starting server")

        self.log.info("Postgres Server already running, will not start again")

    def stop_postgres_server(
            self,
            pgsql_bin_dir,
            pgsql_data_dir):
        """ Stops the postgres server in client
        Args:

            pgsql_bin_dir        (str)  -- postgres bin directory path

            pgsql_data_dir       (str)  -- postgres data directory path


        Returns:

            Returns True on success

            Returns False if the server already stopped

        Raises:

            Exception:

                if server stop operation failes

        """
        return_code = self.get_postgres_status(
            pgsql_bin_dir, pgsql_data_dir)
        if return_code:
            self.log.info("Postgres Server is running, Stopping the server")
            data = {
                'BINDIR': pgsql_bin_dir,
                'DATADIR': pgsql_data_dir,
                'OPERATION': "stop"
            }

            if "unix" in self.machine_object.os_info.lower():
                output = self.machine_object.execute_script(
                    constants.UNIX_POSTGRES_START_STOP,
                    data)
            else:
                output = self.machine_object.execute_script(
                    constants.WINDOWS_POSTGRES_START_STOP,
                    data)

            self.log.debug("Output of Postgres server stop script: %s", output.formatted_output)

            return_code = self.get_postgres_status(
                pgsql_bin_dir, pgsql_data_dir)
            if return_code:
                raise Exception("Unable to Stop the postgres server")
            self.log.info("Successfully Stopped the Postgres Server")
            return True
        else:
            self.log.info("Postgres Server is not running, unable to stop")
            return False

    def get_postgres_status(
            self,
            pgsql_bin_dir,
            pgsql_data_dir):
        """Gets postgres server status
        Args:

            pgsql_bin_dir        (str)  -- postgres bin directory path

            pgsql_data_dir       (str)  -- postgres data directory path

        Returns:

            True  - if PostgreSQl server is running

            False - if PostgreSQL server is not running

        """
        data = {
            'BINDIR': pgsql_bin_dir,
            'DATADIR': pgsql_data_dir,
            'OPERATION': "status"
        }

        if "unix" in self.machine_object.os_info.lower():
            output = self.machine_object.execute_script(constants.UNIX_POSTGRES_STATUS, data)
        else:
            output = self.machine_object.execute_script(constants.WINDOWS_POSTGRES_STATUS, data)

        self.log.debug("Output of Postgres server status check: %s", output.formatted_output)

        if "server is running" not in output.formatted_output:
            self.log.info("Postgres Server is not running")
            return False

        self.log.info("Postgres Server is running")
        return True

    def get_postgres_data_dir(
            self,
            pgsql_bin_dir,
            pgsql_server_password,
            pgsql_server_port):
        """ Gets postgres data directory
        Args:

            pgsql_bin_dir        (str)  -- postgres bin directory path

            pgsql_server_password(str)  -- Postgres server password

            pgsql_server_port    (str)  -- postgres server port number

        Returns:
            Data Directory of PostgreSQL Server

        """
        data = {
            'BINDIR': pgsql_bin_dir,
            'PASSWORD': pgsql_server_password,
            'PORT': pgsql_server_port
        }

        if "unix" in self.machine_object.os_info.lower():
            output = self.machine_object.execute_script(constants.UNIX_POSTGRES_DATADIR, data)
        else:
            output = self.machine_object.execute_script(constants.WINDOWS_POSTGRES_DATADIR, data)

        data_directory = output.formatted_output
        if data_directory == '':
            raise Exception("Failed to get data directory")
        return data_directory

    def get_postgres_bin_dir(
            self,
            client_name,
            instance_name):
        """ Gets postgres binary directory
        Args:

            client_name        (str)    -- client name

            instance_name      (str)    -- postgres instance name

        Returns:
            Binary Directory of PostgreSQL Server

        """

        query = (
            "select attrVal from APP_InstanceProp where componentNameId=(select distinct "
            "instance from APP_Application where clientId=(select id from APP_Client "
            "where name='{0}') and instance in (select id from APP_InstanceName where "
            "name='{1}')) and attrName='PostgreSQL binary file path'".format(client_name, instance_name))
        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()

        if cur:
            self.log.info("Bin directory of postgres instance is fetched Successfully")
            self._postgres_bin_directory = cur[0]
            return cur[0]
        else:
            raise Exception("Failed to get the postgres instance bin directory")

    def check_chunk_commited(self, job_id, log_directory):
        """ Checks for chunk commit in the commserver for the
        initiated job

        Args:
            job_id               (str)  -- Job ID

            log_directory        (str)  -- Commvault Log directory path

        Returns:
            Returns true on success

        """
        cs_machine_object = machine.Machine(
            self._commcell.commserv_name, self._commcell)
        data = {
            'JOBID': job_id,
            'DIR': log_directory
        }
        output = cs_machine_object.execute_script(
            constants.CS_CVD_LOG_CHECK_FOR_CHUNK_COMMIT, data)
        time.sleep(10)
        return output.formatted_output.lower() == 'true'

    def get_subclient_database_list(self, subclient_name, backupset, database_list):
        """Method to get databases associated with a given
        subclient in dumpbased backupset

        Args:
            subclient_name      (str)   -- Subclient Name

            backupset           (obj)   -- Backupset Object

            database_list       (str)   -- list of all databases in the server

        Returns: (list)  --  List of all databases associated with the subclient

        Raises:
            Exception:
                if subclient doesn't exists

        """
        subclient = backupset.subclients.get(subclient_name)
        subclient_list = list(backupset.subclients.all_subclients.keys())
        if subclient.subclient_name not in subclient_list:
            raise Exception("{0} SubClient Does't exist".format(
                subclient.subclient_name))
        default_subclient = backupset.subclients.default_subclient
        if subclient.subclient_name.lower() == default_subclient.lower():
            # Get list of all the subclients content and exclude them from total list
            # of Databases
            self.log.debug("Db list before backup: %s", database_list)
            all_other_sub_clients_contents = list()
            for sbclnt in subclient_list:
                if sbclnt.lower() != default_subclient.lower():
                    self.log.info("Subclient is not default subclient")
                    sub_client_new = backupset.subclients.get(sbclnt)
                    self.log.info("Subc: %s and content: %s", sbclnt, sub_client_new.content)
                    for database in sub_client_new.content:
                        all_other_sub_clients_contents.append(
                            database)
            self.log.info("All other subc content: %s", all_other_sub_clients_contents)
            for db_name in all_other_sub_clients_contents:
                if db_name in database_list:
                    database_list.remove(db_name)
            return database_list
        return subclient.content

    @property
    def postgres_log_directory(self):
        """Returns PostgresBackup.log path in the client"""
        return self.machine_object.join_path(
            self._client.log_directory,
            "PostGresBackup.log")

    @property
    def is_index_v2_postgres(self):
        """Returns True if Postgres index version is V2.

            Returns:
                Returns true if indexing is V2 for postgres.
                Else returns False

            Raises:
                Exception:
                    if failed to get the postgres indexing version

        """
        query = (
            "select attrVal from APP_ClientProp where [componentNameId] "
            "in (select id from APP_Client where name='{0}') and attrName like "
            "'IndexingV2_Postgress'".format(self._client.client_name))
        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()
        if cur:
            index_v2 = cur[0]
            return index_v2 == "1"
        else:
            raise Exception(
                "Failed to get the Postgres Index version")

    def run_restore(
            self,
            paths,
            subclient,
            copy_precedence=None,
            to_time=None,
            clone_env=False,
            clone_options=None,
            media_agent=None,
            table_level_restore=False,
            is_dump_based=False,
            destination_client=None,
            destination_instance=None,
            revert=False,
            skip_status_check=False):
        """Initiates restore job from subclient level and waits for completion

            Args:

                paths                   (list)  --  list of databases to restore

                subclient               (obj)   --  subclient object

                copy_precedence         (int)   --  copy precedence value of storage policy copy
                    default: None

                to_time                 (str)   --  time to retore the contents before
                    format: YYYY-MM-DD HH:MM:SS

                    default: None

                clone_env               (bool)  --  boolean to specify whether the database
                should be cloned or not

                    default: False

                clone_options           (dict)  --  clone restore options passed in a dict

                    default: None

                    Accepted format: {
                                        "stagingLocaion": "/gk_snap",
                                        "forceCleanup": True,
                                        "port": "5595",
                                        "libDirectory": "/opt/PostgreSQL/9.6/lib",
                                        "isInstanceSelected": True,
                                        "reservationPeriodS": 3600,
                                        "user": "postgres",
                                        "binaryDirectory": "/opt/PostgreSQL/9.6/bin"
                                     }

                media_agent         (str)      --  Media agent name

                    default: None

                table_level_restore (bool)     --  table level restore flag

                    default: False

                is_dump_based       (bool)     -- flag to specify dump based restore

                    default: False

                destination_client  (str)   --  Destination client machine name

                    default: None

                destination_instance (str)  --  Destination instance name

                    default: None

                revert (bool)               --  boolean to specify whether to do a
                                                hardware revert in restore
                    default: False

                skip_status_check  (bool)  --  boolean to specify whether to check
                                                            job status
                    default: False

            Returns:

                job            (object)    --  returns the instance of Job class
                for the restore it started

            Raises:

                Exception: If restore job fails to run

        """
        backupset_object = subclient._backupset_object
        self.log.info("#####Starting Restore#####")
        staging_path = None
        if table_level_restore:
            staging_path = "/tmp/testcase"
            if "windows" in self._client.os_info.lower():
                staging_path = "C:\\tmp\\testcase"
        restore_object = backupset_object
        if clone_env or is_dump_based or table_level_restore:
            restore_object = subclient

        if not destination_client:
            destination_client = self._client.client_name
        if not destination_instance:
            destination_instance = self._instance.instance_name

        job = restore_object.restore_postgres_server(
            paths,
            destination_client,
            destination_instance,
            copy_precedence=copy_precedence,
            to_time=to_time,
            clone_env=clone_env,
            clone_options=clone_options,
            media_agent=media_agent,
            table_level_restore=table_level_restore,
            staging_path=staging_path,
            revert=revert)
        self.log.info(
            "Started Restore with Job ID: %s", job.job_id)
        if not skip_status_check:
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore job with error: {0}".format(
                        job.delay_reason
                    )
                )
            self.log.info(
                "Successfully finished restore job")
        self.refresh()
        return job

    def run_backup(self, subclient, backup_type):
        """Initiates the backup job for the specified subclient

        Args:
            subclient            (obj)       -- Subclient object for which backup needs to be run

            backup_type          (str)       -- Type of backup (FULL/INCREMENTAL)

        Returns:
            job                              -- Object of Job class

        Raises:
            Exception:
                if unable to start the backup job

        """
        job = subclient.backup(backup_type)
        self.check_job_status(job)
        return job

    def check_job_status(self, job):
        """Checks the status of job until it is finished and
            raises exception on pending, failure etc.
            Args:
                job         (object)    --  job object
        """
        self.log.info("{1} job started with id: {0}".format(str(job.job_id), job.job_type))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run job with error: {0}".format(
                    job.delay_reason
                )
            )
        self.log.info('{0} job {1} completed successfully'.format(job.job_type, str(job.job_id)))

    def get_metadata(self):
        """ method to collect database information

            Returns:
                dict        --      meta data info of database

            Raises:
                Exception:
                    if unable to get the database list

        """
        # Colecting Meta data after inc backup
        self._get_postgres_database_connection(
            self._postgres_server_url,
            self._postgres_port,
            self._postgres_db_user_name,
            self._postgres_db_password,
            "postgres")
        database_list = self.pgsql_db_object.get_db_list()
        if database_list is None:
            raise Exception(
                "Unable to get the database list."
            )
        # Get the subclient content Info before backup
        self.log.info(
            "Collect information of the subclient content")
        for database in self.ignore_db_list:
            if database in database_list:
                database_list.remove(database)
        return self.generate_db_info(
            database_list,
            self.postgres_server_url,
            self.postgres_port,
            self.postgres_db_user_name,
            self._postgres_db_password)

    def clone_backup_restore(
            self, subclient, clone_options, point_in_time=False,
            destination_client=None, destination_instance=None):
        """method to perform backup/restore and validation of clone feature TCs

            Args:
                subclient       (obj)   --  Subclient Object

                clone_options   (dict)  --  clone restore options passed in a dict

                    default: None

                    Accepted format: {
                                        "stagingLocaion": "/gk_snap",
                                        "forceCleanup": True,
                                        "port": "5595",
                                        "libDirectory": "/opt/PostgreSQL/9.6/lib",
                                        "isInstanceSelected": True,
                                        "reservationPeriodS": 3600,
                                        "user": "postgres",
                                        "binaryDirectory": "/opt/PostgreSQL/9.6/bin"
                                     }

                point_in_time   (bool)  --  flag to check if the restore operation is
                point in time or not

                    default: False

                destination_client  (str)   --  Destination client machine name

                    default: None

                destination_instance (str)  --  Destination instance name

                    default: None

            Raises:
                Exception:
                    if unable to get the database list

                    if database information validation fails

        """

        dbhelper_object = DbHelper(self._commcell)
        pgsql_db_object = database_helper.PostgreSQL(
            self._client.client_hostname,
            self._instance.postgres_server_port_number,
            self._instance.postgres_server_user_name,
            self._postgres_db_password,
            "postgres",
            ssl=self._ssl_enabled,
            ssl_ca=self._ssl_ca,
            ssl_cert=self._ssl_cert,
            ssl_key=self._ssl_key)

        ##################### Running Full Backup ########################
        full_job = dbhelper_object.run_backup(subclient, "FULL")

        # Wait for log backup to complete
        job = dbhelper_object.get_snap_log_backup_job(full_job.job_id)
        self.log.info("Log backup job with ID:%s is now completed", job.job_id)

        # Colecting Meta data
        db_list_before_backup = pgsql_db_object.get_db_list()
        if db_list_before_backup is None:
            raise Exception(
                "Unable to get the database list."
            )
        # Get the subclient content Info before backup
        self.log.info(
            "Collect information of the subclient content")
        for i in self.ignore_db_list:
            if i in db_list_before_backup:
                db_list_before_backup.remove(i)

        db_info_before_full_backup = self.generate_db_info(
            db_list_before_backup,
            self._client.client_hostname,
            self._instance.postgres_server_port_number,
            self._instance.postgres_server_user_name,
            self._postgres_db_password)

        if destination_client and destination_instance:
            self.log.info("Trying to perform cross machine clone restore")
        job_id = None

        if not point_in_time:
            self.log.info("Sleeping for 20 seconds before starting clone restore")
            time.sleep(20)
            job_id = self.run_restore(
                ["/data"],
                subclient,
                clone_env=True,
                clone_options=clone_options,
                destination_client=destination_client,
                destination_instance=destination_instance).job_id
        else:
            # Add some more data and perform a log backup
            self.log.info("Adding some more data")
            self.generate_test_data(
                self._client.client_hostname,
                1,
                20,
                100,
                self._instance.postgres_server_port_number,
                self._instance.postgres_server_user_name,
                self._postgres_db_password,
                True,
                "auto_snap_inc")
            self.log.info("Perfroming log backup")
            dbhelper_object.run_backup(subclient, "INCREMENTAL")
            self.log.info("Sleeping for 20 seconds before starting clone restore")
            time.sleep(20)
            self.log.info("Restoring data upto time:%s", job.end_time)
            job_id = self.run_restore(
                ["/data"],
                subclient,
                clone_env=True,
                clone_options=clone_options,
                to_time=job.end_time).job_id

        # Colecting Meta data
        db_list_after_restore = pgsql_db_object.get_db_list()
        if db_list_after_restore is None:
            raise Exception(
                "Unable to get the database list."
            )
        self.log.info(
            "Collect information of the subclient content after restore")
        for i in self.ignore_db_list:
            if i in db_list_after_restore:
                db_list_after_restore.remove(i)

        self.log.info("Collecting the DB info from cloned database")

        db_info_after_restore = None
        self.log.info("Adding listen address and restarting cloned servers for establishing connections")

        if destination_instance and destination_client:
            destination_client_obj = self._commcell.clients.get(
                destination_client)
            destination_machine = machine.Machine(destination_client_obj)
            clone_config_file_path = self.machine_object.get_logs_for_job_from_file(
                job_id, "POSTGRESBLKRESTORE.log", f".*mv.*/postgresql.conf6 .*/postgresql.conf").strip().split(" ")[-1]
            clone_data_directory = clone_config_file_path.split('postgresql.conf')[0]
            destination_machine.execute_command(f"echo \"listen_addresses='*'\" >> {clone_config_file_path}")
            destination_machine.execute_command(f"echo \"port={clone_options['port']}\" >> {clone_config_file_path}")
            self.stop_postgres_server(self._postgres_bin_directory, clone_data_directory)
            self.start_postgres_server(self._postgres_bin_directory, clone_data_directory)
            destination_instance_obj = destination_client_obj.agents.get(
                'postgresql').instances.get(destination_instance)
            destination_pgsql_obj = PostgresHelper(
                self._commcell, destination_client_obj, destination_instance_obj)
            db_info_after_restore = self.generate_db_info(
                db_list_after_restore,
                destination_client_obj.client_hostname,
                clone_options['port'],
                destination_instance_obj.postgres_server_user_name,
                destination_pgsql_obj._postgres_db_password)
        else:
            clone_config_file_path = self.machine_object.get_logs_for_job_from_file(
                job_id, "POSTGRESBLKRESTORE.log", f".*mv.*/postgresql.conf6 .*/postgresql.conf").strip().split(" ")[-1]
            clone_data_directory = clone_config_file_path.split('postgresql.conf')[0]
            self.machine_object.execute_command(f"echo \"listen_addresses='*'\" >> {clone_config_file_path}")
            self.machine_object.execute_command(f"echo \"port={clone_options['port']}\" >> {clone_config_file_path}")
            self.stop_postgres_server(self._postgres_bin_directory, clone_data_directory)
            self.start_postgres_server(self._postgres_bin_directory, clone_data_directory)
            db_info_after_restore = self.generate_db_info(
                db_list_after_restore,
                self._client.client_hostname,
                clone_options['port'],
                self._instance.postgres_server_user_name,
                self._postgres_db_password)

        # validation using meta data

        self.log.info("Validating the database information collected before SNAP \
            Backup and after clone Restore")
        if not self.validate_db_info(
                db_info_before_full_backup, db_info_after_restore):
            raise Exception(
                "Database information validation failed."
            )
        else:
            self.log.info(
                "Database information validation passed successfully")

    def blocklevel_backup_restore(self, subclient, postgres_data_population_size, tc_type=None, proxy_client=None):
        """method to perform backup/restore and validation of block level feature TCs

            Args:
                subclient                       (obj)   --  Subclient Object

                postgres_data_population_size   (list)  --  list containing information
                of data population size

                tc_type                         (str)   --  testcase type

                    default: None

                    Accepted values: ACC1/INCREMENTAL/SYNTH_FULL/POINT_IN_TIME/INDEX_DELETE_BLB/INDEX_DELETE_SNAP

                proxy_client                    (str)   --  Proxy client name for backup copy job

                    default: None

            Raises:
                Exception:
                    if unable to get the database list

                    if server fails to stop

                    if database information validation fails

                    if data is not restored from snap copy

                    if failed to run mount/unmount job

                    if Unable to verify the mounted snap from synthfull job

        """
        PROXY_BLB = "proxy_blb"

        if tc_type is None:
            tc_type = "ACC1"
        if proxy_client:
            tc_type = PROXY_BLB

        dbhelper_object = DbHelper(self._commcell)
        pgsql_db_object = database_helper.PostgreSQL(
            self._client.client_hostname,
            self._instance.postgres_server_port_number,
            self._instance.postgres_server_user_name,
            self._postgres_db_password,
            "postgres",
            ssl=self._ssl_enabled,
            ssl_ca=self._ssl_ca,
            ssl_cert=self._ssl_cert,
            ssl_key=self._ssl_key)
        postgres_data_directory = self.get_postgres_data_dir(
            self._instance.postgres_bin_directory,
            self._postgres_db_password,
            self._instance.postgres_server_port_number)

        ########################## SNAP Backup/Restore Operation ##########
        self.log.info("##### SNAP Backup/Restore Operations #####")

        self.log.info("Generating Test Data")
        self.generate_test_data(
            self._client.client_hostname,
            postgres_data_population_size[0],
            postgres_data_population_size[1],
            postgres_data_population_size[2],
            self._instance.postgres_server_port_number,
            self._instance.postgres_server_user_name,
            self._postgres_db_password,
            True,
            "auto_snap")
        self.log.info("Test Data Generated successfully")

        ###################### Running Full Backup ########################
        self.log.info("Starting FULL backup job")
        full_job = dbhelper_object.run_backup(subclient, "FULL")

        # Wait for log backup to complete
        full_job_log = dbhelper_object.get_snap_log_backup_job(full_job.job_id)
        self.log.info("Log backup job with ID:%s is now completed", full_job_log.job_id)

        db_info_before_full_backup = None
        db_info_before_inc_backup = None

        # Colecting Meta data
        db_list_before_backup = pgsql_db_object.get_db_list()
        if db_list_before_backup is None:
            raise Exception(
                "Unable to get the database list."
            )
        # Get the subclient content Info before backup
        self.log.info(
            "Collect information of the subclient content")
        for database in self.ignore_db_list:
            if database in db_list_before_backup:
                db_list_before_backup.remove(database)
        db_info_before_full_backup = self.generate_db_info(
            db_list_before_backup,
            self._client.client_hostname,
            self._instance.postgres_server_port_number,
            self._instance.postgres_server_user_name,
            self._postgres_db_password)

        if tc_type.lower() in ["incremental", "synth_full", "point_in_time"]:
            # Add more data before Incremental
            self.log.info("Adding more data to run incremental backup")
            self.generate_test_data(
                self._client.client_hostname,
                1,
                5,
                100,
                self._instance.postgres_server_port_number,
                self._instance.postgres_server_user_name,
                self._postgres_db_password,
                True,
                "auto_snap_inc")

            # run incremental backup
            self.log.info("Starting Incremental backup job")
            inc_job = dbhelper_object.run_backup(subclient, "Incremental", inc_with_data=True)
            # Wait for log backup to complete
            inc_job_log = dbhelper_object.get_snap_log_backup_job(inc_job.job_id)
            self.log.info("Log backup job with ID:%s is now completed", inc_job_log.job_id)

            # Colecting Meta data after inc backup
            db_list_before_backup = pgsql_db_object.get_db_list()
            if db_list_before_backup is None:
                raise Exception(
                    "Unable to get the database list."
                )
            # Get the subclient content Info before backup
            self.log.info(
                "Collect information of the subclient content")
            for database in self.ignore_db_list:
                if database in db_list_before_backup:
                    db_list_before_backup.remove(database)
            db_info_before_inc_backup = self.generate_db_info(
                db_list_before_backup,
                self._client.client_hostname,
                self._instance.postgres_server_port_number,
                self._instance.postgres_server_user_name,
                self._postgres_db_password)

        if "native" not in subclient.snapshot_engine_name.lower():
            if tc_type.lower() not in ["synth_full", "index_delete_blb", "index_delete_snap", PROXY_BLB]:
                self.log.info("Snap engine is not native.")
                self.log.info("Sleeping for 20 seconds before starting restore")
                time.sleep(20)

                self.cleanup_database_directories()

                # Running FS Restore
                full_job_end_time = None
                if "point_in_time" in tc_type.lower():
                    self.log.info("Starting PIT restore")
                    full_job_end_time = full_job.end_time
                job = self.run_restore(
                    ["/data"],
                    subclient,
                    to_time=full_job_end_time,
                    media_agent=self._client.client_name)

                del pgsql_db_object
                pgsql_db_object = database_helper.PostgreSQL(
                    self._client.client_hostname,
                    self._instance.postgres_server_port_number,
                    self._instance.postgres_server_user_name,
                    self._postgres_db_password,
                    "postgres",
                    ssl=self._ssl_enabled,
                    ssl_ca=self._ssl_ca,
                    ssl_cert=self._ssl_cert,
                    ssl_key=self._ssl_key)

                # Colecting Meta data
                db_list_after_restore = pgsql_db_object.get_db_list()
                if db_list_after_restore is None:
                    raise Exception(
                        "Unable to get the database list."
                    )
                self.log.info(
                    "Collect information of the subclient content after restore")
                for database in self.ignore_db_list:
                    if database in db_list_after_restore:
                        db_list_after_restore.remove(database)

                db_info_after_restore = self.generate_db_info(
                    db_list_after_restore,
                    self._client.client_hostname,
                    self._instance.postgres_server_port_number,
                    self._instance.postgres_server_user_name,
                    self._postgres_db_password)

                # validation using meta data

                self.log.info("Validating the database information collected before SNAP \
                    Backup and after Inplace Restore for SNAP Backup")
                # validate subclient content information collected before backup
                # and after restore
                return_code = None
                if tc_type.lower() not in ["point_in_time", "acc1"]:
                    return_code = self.validate_db_info(
                        db_info_before_inc_backup, db_info_after_restore)
                else:
                    return_code = self.validate_db_info(
                        db_info_before_full_backup, db_info_after_restore)
                if not return_code:
                    raise Exception(
                        "Database information validation failed."
                    )
                else:
                    self.log.info(
                        "Database information validation passed successfully")

                self.log.info("Validating if the data is restored from snap copy or not")
                if not dbhelper_object.check_if_restore_from_snap_copy(job):
                    raise Exception(
                        "Data is not restored from snap copy."
                    )
                self.log.info("validation passed..!! Data is restored form snap copy.")
            backup_copy_job_obj = None
            ###### Run backup copy job #########
            self.log.info(
                "Running backup copy job for storage policy: %s",
                subclient.storage_policy)
            copy_precedence = dbhelper_object.run_backup_copy(subclient.storage_policy)
            self.log.info("Copy precedence of 'primary snap' copy is: %s", copy_precedence)
            backup_copy_job_obj = dbhelper_object.get_backup_copy_job(full_job.job_id)
        else:
            self.log.info(
                (
                    "Native Snap engine is being run. backup "
                    "copy job will run inline to snap backup"))
            self.log.info("Getting the backup job ID of backup copy job")
            backup_copy_job_obj = dbhelper_object.get_backup_copy_job(inc_job.job_id)

        self.log.info("Job ID of backup copy Job is: %s", backup_copy_job_obj.job_id)
        if PROXY_BLB in tc_type.lower():
            if not dbhelper_object.check_if_backup_copy_run_on_proxy(
                    backup_copy_job_obj.job_id, self._commcell.clients.get(proxy_client)):
                raise Exception("Proxy client was not used for backup copy")

        if "synth_full" in tc_type.lower():
            ############ run synthfull backup jobs ######
            self.log.info("Starting synthetic full backup.")
            synth_job = dbhelper_object.run_backup(subclient, "synthetic_full")
            self.log.info("Synthetic full backup %s is finished", synth_job.job_id)

            self.log.info(
                ("Running data aging on storage policy:%s copy:primary to "
                 "make sure the restore is triggered from Synthfull backup"),
                subclient.storage_policy)

            common_utils = idautils.CommonUtils(self._commcell)
            data_aging_job = common_utils.data_aging(
                subclient.storage_policy, "primary", False)
            self.log.info("Dataaging job run is:%s", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging job with error: {0}".format(
                        data_aging_job.delay_reason
                    )
                )
            self.log.info("Data aging job is finished")

            ######### Synth full validation #########
            self.log.info("Mounting the snap in client at:/tmp/testcase_mount")
            volume_id = int(dbhelper_object.get_volume_id(synth_job.job_id)[0][0])
            self.log.info("Volume ID: %s", volume_id)
            # mount the snap in the client
            array_mgmt_object = self._commcell.array_management
            self.machine_object.execute_command("mkdir -p /tmp/testcase_mount")
            mount_job = array_mgmt_object.mount(
                [[volume_id]],
                self._client.client_name,
                "/tmp/testcase_mount")
            self.log.info(
                "Mounting the snapshot in the client with job:%s",
                mount_job.job_id)
            if not mount_job.wait_for_completion():
                raise Exception(
                    "Failed to run mount job with error: {0}".format(
                        mount_job.delay_reason
                    )
                )
            self.log.info("Succesfully mounted the snapshot in the client")

            # Validate the data
            # Run find command to check if the data is corrupted
            command = ("find /tmp/testcase_mount -type f -print "
                       "-exec cp -r {} /dev/null \; > readsnapdata")
            output = self.machine_object.execute_command(command)
            if output.exception_message != '':
                raise Exception("Unable to verify the mounted snap from synhfull job")
            self.log.info("Synthfull job is verified")

            # Unmount the snap
            self.log.info("Unmounting snapshot")
            unmount_job = array_mgmt_object.unmount(
                [[volume_id]])
            self.log.info(
                "UnMounting the snapshot in the client with job:%s",
                unmount_job.job_id)
            if not unmount_job.wait_for_completion():
                raise Exception(
                    "Failed to run unmount job with error: {0}".format(
                        unmount_job.delay_reason
                    )
                )
            self.log.info("Snapshot is unmounted")

            #### Run incremental with data + backup after synthfull
            self.log.info("Running a incremental backup after the synthful job")
            self.log.info("Adding more data to run incremental backup")
            self.generate_test_data(
                self._client.client_hostname,
                1,
                5,
                100,
                self._instance.postgres_server_port_number,
                self._instance.postgres_server_user_name,
                self._postgres_db_password,
                True,
                "auto_snap_inc_after_synthfull")

            # run incremental backup
            self.log.info("Starting Incremental backup job")
            inc_job = dbhelper_object.run_backup(subclient, "Incremental", inc_with_data=True)
            # Wait for log backup to complete
            inc_job_log = dbhelper_object.get_snap_log_backup_job(inc_job.job_id)
            self.log.info("Log backup job with ID:%s is now completed", inc_job_log.job_id)

            # Colecting Meta data after inc backup
            db_list_before_backup = pgsql_db_object.get_db_list()
            if db_list_before_backup is None:
                raise Exception(
                    "Unable to get the database list."
                )
            # Get the subclient content Info before backup
            self.log.info(
                "Collect information of the subclient content")
            for database in self.ignore_db_list:
                if database in db_list_before_backup:
                    db_list_before_backup.remove(database)
            db_info_before_inc_backup = self.generate_db_info(
                db_list_before_backup,
                self._client.client_hostname,
                self._instance.postgres_server_port_number,
                self._instance.postgres_server_user_name,
                self._postgres_db_password)

            if "native" not in subclient.snapshot_engine_name.lower():
                ###### Run backup copy job #########
                self.log.info(
                    "Running backup copy job for storage policy: %s",
                    subclient.storage_policy)
                copy_precedence = dbhelper_object.run_backup_copy(subclient.storage_policy)
                self.log.info("Copy precedence of 'primary snap' copy is: %s", copy_precedence)

            else:
                self.log.info(
                    (
                        "Native Snap engine is being run. backup "
                        "copy job will run inline to snap backup"))
                self.log.info("Getting the backup job ID of backup copy job")
                job = dbhelper_object.get_backup_copy_job(inc_job.job_id)
                self.log.info("Job ID of backup copy Job is: %s", job.job_id)

        if "index_delete" in tc_type.lower():
            self.log.info("Running Data aging as Index delete case being run")
            common_utils = idautils.CommonUtils(self._commcell)
            data_aging_job = common_utils.data_aging(
                subclient.storage_policy, "primary", False)
            self.log.info("Dataaging job run is:%s", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging job with error: {0}".format(
                        data_aging_job.delay_reason
                    )
                )
            self.log.info("Data aging job is finished")

        if tc_type.lower() not in ["synth_full", "index_delete_snap"]:
            ############ Table level restore ############
            ######### Drop two tables from first database ########
            database_name = "auto_snap_testdb_0"
            if tc_type.lower() in ["incremental", "synth_full"]:
                database_name = "auto_snap_inc_testdb_0"
            self.drop_table(
                "testtab_1",
                self._client.client_hostname,
                self._instance.postgres_server_port_number,
                self._instance.postgres_server_user_name,
                self._postgres_db_password,
                database_name)
            self.drop_view("test_view_0", database=database_name)

            self.log.info("Collecting meta data to validate data after restore.")
            table_info_before = self.generate_db_info(
                [database_name],
                self._client.client_hostname,
                self._instance.postgres_server_port_number,
                self._instance.postgres_server_user_name,
                self._postgres_db_password)
            self.drop_table(
                "testtab_0",
                self._client.client_hostname,
                self._instance.postgres_server_port_number,
                self._instance.postgres_server_user_name,
                self._postgres_db_password,
                database_name)

            if "index_delete_blb" in tc_type.lower():
                self.log.info("Deleting Index before table level restore")
                if self.is_index_v2_postgres:
                    dbhelper_object.delete_v2_index_restart_service(subclient._backupset_object)
                else:
                    dbhelper_object.delete_v1_index_restart_service(subclient)

            # start table level restore
            self.log.info("starting table level restore.")
            self.run_restore(
                ["/%s/public/testtab_0/" % (database_name)],
                subclient,
                table_level_restore=True)

            self.log.info("collecting meta data to validate.")
            table_info_after = self.generate_db_info(
                [database_name],
                self._client.client_hostname,
                self._instance.postgres_server_port_number,
                self._instance.postgres_server_user_name,
                self._postgres_db_password)

            return_code = self.validate_db_info(
                table_info_after, table_info_before)
            if not return_code:
                raise Exception(
                    "Database info validation failed after table level restore."
                )
            else:
                self.log.info(
                    "Database information validation passed successfully for table level restore")

        ############ restore from primary copy ############
        self.log.info("Sleeping for 20 seconds before starting restore")
        time.sleep(20)
        storage_policy_object = self._commcell.storage_policies.get(
            subclient.storage_policy)
        copy_precedence = storage_policy_object.get_copy_precedence("primary")

        self.cleanup_database_directories()

        if "index_delete" in tc_type.lower():
            self.log.info("Deleting Index restore")
            if self.is_index_v2_postgres:
                dbhelper_object.delete_v2_index_restart_service(subclient._backupset_object)
            else:
                dbhelper_object.delete_v1_index_restart_service(subclient)

        # Running FS Restore
        self.log.info(
            "Restoring database from primary copy with precedence:%s",
            copy_precedence)
        full_job_end_time = None
        if "point_in_time" in tc_type.lower():
            full_job_end_time = full_job.end_time
            copy_precedence = None
        self.run_restore(
            ["/data"],
            subclient,
            copy_precedence=copy_precedence,
            to_time=full_job_end_time,
            media_agent=self._client.client_name if (
                    "index_delete" in tc_type.lower() and not self.is_index_v2_postgres) else None)

        del pgsql_db_object
        pgsql_db_object = database_helper.PostgreSQL(
            self._client.client_hostname,
            self._instance.postgres_server_port_number,
            self._instance.postgres_server_user_name,
            self._postgres_db_password,
            "postgres",
            ssl=self._ssl_enabled,
            ssl_ca=self._ssl_ca,
            ssl_cert=self._ssl_cert,
            ssl_key=self._ssl_key)

        # Colecting Meta data
        db_list_after_restore = pgsql_db_object.get_db_list()
        if db_list_after_restore is None:
            raise Exception(
                "Unable to get the database list."
            )
        self.log.info(
            "Collect information of the subclient content after restore")
        for database in self.ignore_db_list:
            if database in db_list_after_restore:
                db_list_after_restore.remove(database)

        db_info_after_restore = self.generate_db_info(
            db_list_after_restore,
            self._client.client_hostname,
            self._instance.postgres_server_port_number,
            self._instance.postgres_server_user_name,
            self._postgres_db_password)

        # validation using meta data

        self.log.info("Validating the database information collected before Full \
            Backup and after Inplace Restore for FSBased Backup")
        # validate subclient content information collected before backup
        # and after restore
        return_code = None
        if tc_type.lower() not in ["point_in_time", "acc1", "index_delete_snap", "index_delete_blb", PROXY_BLB]:
            return_code = self.validate_db_info(
                db_info_before_inc_backup, db_info_after_restore)
        else:
            return_code = self.validate_db_info(
                db_info_before_full_backup, db_info_after_restore)
        if not return_code:
            raise Exception(
                "Database information validation failed."
            )
        else:
            self.log.info(
                "Database information validation passed for primary copy restore")

        self.log.info("Deleting Automation Created databases")
        self.cleanup_tc_db(
            self._client.client_hostname,
            self._instance.postgres_server_port_number,
            self._instance.postgres_server_user_name,
            self._postgres_db_password,
            "auto")

    def set_port_and_listen_address(self, job_id=None, PortForClone=None):
        """method to set the clone port and the listen address in the postgresql.conf file in the cloned data directory

        Args:
            job_id       (int)   -- The clone restore job_id

                default : None

            PortForClone (int)   -- The port for the cloned instance

                default : None
        """
        self.log.info("Adding listen address, port and restarting cloned servers for establishing connections")
        clone_config_file_path = self.machine_object.get_logs_for_job_from_file(
            job_id, "POSTGRESBLKRESTORE.log", f".*mv.*/postgresql.conf6 .*/postgresql.conf").strip().split(" ")[-1]
        clone_data_directory = clone_config_file_path.split('postgresql.conf')[0]
        self.machine_object.execute_command(f"echo \"listen_addresses='*'\" >> {clone_config_file_path}")
        self.machine_object.execute_command(f"echo \"port={PortForClone}\" >> {clone_config_file_path}")
        self.stop_postgres_server(self._postgres_bin_directory, clone_data_directory)
        self.start_postgres_server(self._postgres_bin_directory, clone_data_directory)

    def cleanup_database_directories(self, archive_log_dir=None):
        """ method to remove data and wal directory before fsbased restore
            Args:

                archive_log_dir     (str)   --  archive log directory

                    default: None
        """
        data_directory = self.get_postgres_data_dir(
            self._postgres_bin_directory,
            self._postgres_db_password,
            self._postgres_port)
        tablespace_path_list = self.get_tablespace_paths()
        if self.get_postgres_status(
                self._postgres_bin_directory,
                data_directory):
            self.log.info("Server is still running, trying to stop server")
            self.stop_postgres_server(
                self._postgres_bin_directory,
                data_directory)
        self.log.info("Cleaning postgres data directory")
        self.machine_object.remove_directory(data_directory)
        self.log.info("Cleaning up Tablespace directory")
        for path in tablespace_path_list:
            self.machine_object.remove_directory(path)
            self.log.info("Tablespace directory removed:%s", path)
        if not archive_log_dir:
            archive_log_dir = self._instance.postgres_archive_log_directory
        self.log.info("Data directory removed")
        self.log.info("Cleaning postgres wal directory")
        self.machine_object.remove_directory(archive_log_dir)
        self.log.info("WAL directory removed")

    def get_replication_job(self, backup_job):
        """ method to fetch the replication job associated with
        live sync operation from commserv database

            Args:
                backup_job     (obj)    -- backup job object

            Returns:
                job            (obj)    --  returns replication job object started
                by the backup job

            Raises:
                Exception
                    if unable to get replication job ID

        """
        backupset_id = self._instance.backupsets.get('fsbasedbackupset').backupset_id
        query = (
            "select jobId from JMRestoreStats where bkpSetID={0} and servStartTime>={1} order by jobId DESC".format(
                backupset_id,
                backup_job.summary['jobEndTime']))
        count = 0
        while True:
            count += 1
            self._csdb.execute(query)
            cur = self._csdb.fetch_one_row()
            if cur:
                if cur[0] != '':
                    return self._commcell.job_controller.get(cur[0].strip())
                else:
                    if count >= 60:
                        raise Exception("Failed to get the replication Job ID")
                    self.log.info("Sleeping for 30 seconds as replication job is not complete yet")
                    time.sleep(30)
            else:
                raise Exception(
                    "Failed to get the replication Job ID")

    def check_postgres_recovery_mode(self):
        """checks if the postgres server is in recovery mode

        Returns:
            returns True if the server is in recovery mode else returns False

        Raises:
            Exception:
                if unable to get recovery flag

        """
        try:
            postgres_database_object = database_helper.PostgreSQL(
                self._client.client_hostname,
                self._instance.postgres_server_port_number,
                self._instance.postgres_server_user_name,
                self._postgres_db_password,
                "postgres",
                ssl=self._ssl_enabled,
                ssl_ca=self._ssl_ca,
                ssl_cert=self._ssl_cert,
                ssl_key=self._ssl_key)
            query = "select pg_is_in_recovery();"
            result = postgres_database_object.execute(query)
            return result.rows[0][0]
        except Exception:
            self.log.error("Exception in getting recovery flag")
            raise Exception("Unable to get recovery flag")

    def create_path_for_tablespace(self, pgsql_datadir):
        """method to create tablespace directory

        Args:
            pgsql_datadir   (str)  -- postgresql data directory path

        Returns:
            tablespace_dir  (str)  -- Path of the tablespace directory

        Raises:
            Exception:
                if unable create tablespace directory

        """

        try:
            if "unix" in self.machine_object.os_info.lower():
                lastslash = pgsql_datadir.rfind('/')
                tablespace_dir = pgsql_datadir[0:lastslash + 1]
                tablespace_dir = ("%sautotabspace") % pgsql_datadir
                self.machine_object.create_directory(tablespace_dir)
                cmd = "chown -Rf postgres:postgres %s" % str(tablespace_dir)
                self.machine_object.execute_command(cmd)
            else:
                lastslash = pgsql_datadir.rfind('\\')
                tablespace_dir = pgsql_datadir[0:lastslash + 1]
                tablespace_dir = ("%sautotabspace") % pgsql_datadir
                self.machine_object.create_directory(tablespace_dir)
            return tablespace_dir
        except Exception:
            self.log.error("Exception in creating tablespace directory")
            raise Exception("Unable to create tablespace directory")

    @property
    def is_pg_in_recovery(self):
        """ checks if postgres server is in recovery

            Returns:
                True if postgres server is in recovery else returns False

            Raises:
                Exception:
                if unable to get recovery info

        """
        try:
            postgres_database_object = self._get_postgres_database_connection(
                self._postgres_server_url,
                self._postgres_port,
                self._postgres_db_user_name,
                self._postgres_db_password,
                "postgres")

            query = "select pg_is_in_recovery()"
            postgres_response = postgres_database_object.execute(query)
            return postgres_response.rows[0][0]
        except Exception as exp:
            raise Exception("Exception {0} in checking recovery mode".format(str(exp)))

    @property
    def is_streaming_replication(self):
        """ checks if postgres server is in streaming replication

            Returns:
                True if postgres server is in streaming replication else returns False

            Raises:
                Exception:
                if unable to get streaming replication info

        """
        try:
            postgres_database_object = self._get_postgres_database_connection(
                self._postgres_server_url,
                self._postgres_port,
                self._postgres_db_user_name,
                self._postgres_db_password,
                "postgres")

            query = "select state from pg_stat_replication;"
            postgres_response = postgres_database_object.execute(query)
            if len(postgres_response.rows) == 0:
                return False
            if "streaming" in postgres_response.rows[0][0].lower():
                return True
            return False
        except Exception as exp:
            raise Exception("Exception {0} in checking replication info".format(str(exp)))

    def is_backup_run_on_standby(self, job_id, backup_phase='DATA'):
        """ method to check if the backup is run on standby node or not

        Args:
            job_id  (str)       --  Backup job ID

            backup_phase(str)   --  Backup phase to check for

                Accepted values: DATA/LOG

                default: DATA

        Returns:
            True if the backup phase specified is run on standby node
            False otherwise

        """
        command = ""
        log_path = self._client.log_directory
        if 'data' in backup_phase.lower():
            log_path = self.machine_object.join_path(log_path, 'PostGresBackupParent.log')
        else:
            log_path = self.machine_object.join_path(log_path, 'PostGresLogBackupParent.log')
        command = f"cat {log_path} | grep {job_id} | grep \'Running backup on secondary server\'"
        output = self.machine_object.execute_command(command)
        if output.exception_message != '':
            raise Exception("Unable to run the command on client machine")
        if str(job_id) in output.formatted_output:
            return True
        return False

    def get_standby_client_name(self, instance_id):
        """gets the client name of the standby instance

        Args:
            instance_id(int)    --  standby instance id
        """
        query = (
            "select name from APP_Client where id = (select DISTINCT(clientId) "
            f"from app_application where instance={instance_id})")
        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()
        if cur:
            return cur[0]
        else:
            raise Exception("Failed to get the standby client name from database")

    def get_tablespace_paths(self):
        """
        Get the list of paths of all tablespaces in pg server

            Returns:
                List - list of tablespace dircetories

            Raises:
                Exception:
                if unable to get tablespace paths

        """
        tablespace_paths = list()
        try:
            postgres_database_object = self._get_postgres_database_connection(
                self._postgres_server_url,
                self._postgres_port,
                self._postgres_db_user_name,
                self._postgres_db_password,
                "postgres")
            query = ("select pg_tablespace_location(oid) from pg_tablespace "
                     "where pg_tablespace_location(oid)!=''")
            postgres_response = postgres_database_object.execute(query)
            for row in postgres_response.rows:
                tablespace_paths.append(row[0])
            return tablespace_paths
        except Exception as exp:
            raise Exception("Exception {0} in get_tablespace_paths".format(str(exp)))

    def refresh(self):
        """Refresh DB connection"""
        self._pgsql_db_object = None
        self._pgsql_custom_db_object = None

    def get_wal_seg_size(self):
        """ Gets postgres wal segment size from server
        Returns:
            wal_seg_size (int) : wal segment size in MB
        Raises:
            Exception: if wal segment size cannot be retrieved
        """
        try:
            postgres_database_object = self._get_postgres_database_connection(
                self._postgres_server_url,
                self._postgres_port,
                self._postgres_db_user_name,
                self._postgres_db_password,
                "template1")
            query = "show wal_segment_size;"
            postgres_response = postgres_database_object.execute(query)
            wal_seg_size = postgres_response.rows[0][0]
            self.log.info("Wal segment size is %s", wal_seg_size)
            if "MB" in wal_seg_size:
                wal_seg_size = int(wal_seg_size[:-2])
            elif "GB" in wal_seg_size:
                wal_seg_size = int(wal_seg_size[:-2]) * 1024
            else:
                raise Exception("wal segment size not in MB or GB")
            return wal_seg_size
        except Exception as exp:
            raise Exception("Exception {0} in getting wal segment size".format(str(exp)))

    def switch_log(self, count=2):
        """ Performs switch log operation for transaction logs
            Args:
                count(int):   Number of times log switch should be performed
            Raises:
                Exception:    If switch log fail
        """
        try:
            postgres_database_object = self._get_postgres_database_connection(
                self._postgres_server_url,
                self._postgres_port,
                self._postgres_db_user_name,
                self._postgres_db_password,
                "template1")
            self.log.info("PG Version is %s", self._instance.postgres_version)
            if int(self._instance.postgres_version.split(".")[0]) < 10:
                query = "select pg_switch_xlog();"
            else:
                query = "select pg_switch_wal();"
            while count > 0:
                self.create_table(
                    "tab_60485",
                    self._client.client_hostname,
                    self._postgres_port,
                    self._postgres_db_user_name,
                    self._postgres_db_password,
                    "template1")
                postgres_database_object.execute(query)
                self.drop_table(
                    "tab_60485",
                    self._client.client_hostname,
                    self._postgres_port,
                    self._postgres_db_user_name,
                    self._postgres_db_password,
                    "template1")
                postgres_database_object.execute(query)
                count -= 2
        except Exception as exp:
            raise Exception("Exception {0} in switch log".format(str(exp)))

    def schedule_details(self, subclient_id):
        """Finds details of automatic schedules for a specified subclient
            Args:
                subclient_id(int)   : subclient id
            Returns:
                disk_threshold(int) : Minimum value of disk threshold to trigger log backup
                log_threshold(int)  : Minimum value of log threshold to trigger log backup
            Raises:
                Exception: If no automatic schedule exists or is in enabled state
        """
        try:
            query = "select scheduleId from SubClientAutoSchedules " \
                    "where subClientId='{}'".format(subclient_id)
            self._csdb.execute(query)
            cur = self._csdb.fetch_all_rows()
            if cur:
                disk_threshold_values = []
                log_threshold_values = []
                for num in enumerate(cur):
                    query = "select xmlvalue from TM_SubTaskXMLOptions where " \
                            "subTaskId = {};".format(num[1][0])
                    self.log.info("Query %d for subclient is %s", num[0], query)
                    self._csdb.execute(query)
                    cur2 = self._csdb.fetch_one_row()
                    if cur2:
                        data = cur2[0]
                        if 'diskUsedPercent' in data and 'logFileNum' in data:
                            diskuse_index = int(re.split(r'\W+', data).index('diskUsedPercent'))
                            if int(re.split(r'\W+', data)[diskuse_index + 4]) == 1:
                                disk_percent = int(re.split(r'\W+', data)[diskuse_index + 2])
                                disk_threshold_values.append(disk_percent)
                            log_index = int(re.split(r'\W+', data).index('logFileNum'))
                            if int(re.split(r'\W+', data)[log_index + 4]) == 1:
                                log_count = int(re.split(r'\W+', data)[log_index + 2])
                                log_threshold_values.append(log_count)
            else:
                raise Exception("No schedule associated for the subclient")
            if len(disk_threshold_values) > 0 and len(log_threshold_values) > 0:
                disk_threshold = min(disk_threshold_values)
                log_threshold = min(log_threshold_values)
                self.log.info("Space threshold = %d and log threshold = %d",
                              disk_threshold, log_threshold)
            else:
                raise Exception("Schedules are in disabled state")
            return disk_threshold, log_threshold
        except Exception as exp:
            raise Exception("Exception {0} in getting schedule details".format(str(exp)))

    def get_afileid(self, job_id, file_type=1, flags=0):
        """Gets afile id of a backup for given job id, file type and flags
                Args:
                    job_id (int)  -- Backup Job ID
                    file_type(int)-- file type of the archfile
                        Accepted values = 1 for data and 4 for log. Default is 1
                    flags (int)   -- flags for the arch file per cs db table
                        Accepted values = any integer . it varies based on type of
                        backup and operation type. Default is 0
                Returns:
                    afileid (int) -- id for first record from archfile table
                                     meeting the criteria specified
                Raises:
                    Exception:
                        If no archfile id is retrieved
        """
        if flags > 0:
            query = ("select id from archfile where jobid={0} and fileType={1} and "
                     "flags={2}".format(job_id, file_type, flags))
        else:
            query = ("select id from archfile where jobid={0} and "
                     "fileType={1}".format(job_id, file_type))
        self.log.info("Query used is :%s", query)
        self._csdb.execute(query)
        cur = self._csdb.fetch_all_rows()
        if cur:
            cur.reverse()
            afileid = cur[len(cur) - 1][0], cur[len(cur) - 2][0]
            return afileid
        raise Exception("Failed to get the arch file ID from cs db")

    def confirm_logging(self, job_id, log_file_name, search_term, pattern):
        """Check if specified pattern exists in log for given job id and search term
        Args:
            jobid (int)         -- job id of restore operation
            log_file_name (str) -- name of the log file to check
            search_term (str)   -- term to search in the log file
            pattern (str)       -- pattern to check in the log file
        Raises:
            Exception:
                If pattern is not found in log for given job id and search term
        """
        output = self.machine_object.get_logs_for_job_from_file(
            job_id, log_file_name, search_term)
        if pattern not in output:
            raise Exception("Confirming copy used from commvault log failed."
                            "Jobid:{0} log:{1} searched term:{2} pattern:{3} "
                            "Output:{4}".format(job_id, log_file_name, search_term,
                                                pattern, output))
        self.log.info("Log verification completed fine")

    def run_aux_copy(self, storage_policy, fsbased=True):
        """ Perform aux copy for specified storage policy
        Args:
            storage_policy(str) -- storage policy for which aux copy need to be run
            fsbased (bool)      -- True to indicate fsbased backupset and False to
            indicate dumpbased. Default is True.
        """
        storage_policy_object = self._commcell.storage_policies.get(storage_policy)
        storage_policy_object.run_aux_copy("automation_copy")
        self.log.info("Aux copy for SP %s completed", storage_policy)
        if fsbased and not self._instance.log_storage_policy == storage_policy:
            self.log.info("Run aux copy for SP %s", self._instance.log_storage_policy)
            storage_policy_object.run_aux_copy("automation_copy")
            self.log.info("Aux copy for SP %s completed", self._instance.log_storage_policy)

    def prepare_aux_copy(self, storage_policy, fsbased=True):
        """Prepares copy named automation_copy for storage policy and confirms
         copy precendence is same for data and log SPs for fsbased backupset
        Args:
            storage_policy (str) -- Name of the storage policy
            fsbased (bool)       -- True to indicate fsbased backupset and False to
            indicate dumpbased. Default is True.
        Returns:
            data_cp (int) -- copy precedence of aux copy named automation_copy
        Raises:
            Exception:
                If copy precedence of data and log SP aux copy are not same
        """
        dbhelper_object = DbHelper(self._commcell)
        data_cp = dbhelper_object.prepare_aux_copy_restore(storage_policy)
        if fsbased and not self._instance.log_storage_policy == storage_policy:
            log_cp = dbhelper_object.prepare_aux_copy_restore(self._instance.log_storage_policy)
            if not data_cp == log_cp:
                raise Exception("Copy precedence for automation_copy aux copy "
                                "differ for data and log SPs")
        self.log.info("Copy precedence is %d", data_cp)
        return data_cp

    def create_automatic_log_backup_schedule_policy(
            self, name="postgres_1min_rpo", association=None,
            disk_use_threshold=None, number_of_log_files=None):
        """method to create automatic log backup schedule policy

        Args:
            name    (str)       -- Name of the schedule policy

            association (list)  -- Association to the schedule policy
                default: None (automatically associated to fs subclient level)

                format:
                    association = [{
                                    "clientName": client_name,
                                    "backupsetName": "FSBasedBackupSet",
                                    "subclientName": "default",
                                    "instanceName": instanceName,
                                    "appName": "PostgreSQL"
                                }]

            disk_use_threshold  (int)%   --  Disk threshold value (within 1 to 100)
                default: None

            number_of_log_files (int)   --  Max number of log files
                default: None

        """
        pattern = [{'name': 'Dummy_name',
                    'pattern': {"freq_type":
                                    'automatic'
                                }}]
        if disk_use_threshold:
            pattern[0]['pattern']['disk_use_threshold'] = disk_use_threshold
        if number_of_log_files:
            pattern[0]['pattern']['number_of_log_files'] = number_of_log_files
        types = [{"appGroupName": "PostgreSQL"}]
        if not association:
            association = [{
                "clientName": self._client.client_name,
                "instanceName": self._instance.instance_name,
                "appName": "PostgreSQL",
                "backupsetName": "FSBasedBackupSet",
                "subclientName": "default"
            }]
        self._commcell.schedule_policies.add(
            name=name, policy_type='Data Protection',
            associations=association, schedules=pattern, agent_type=types)

    def get_postgres_db_obj(self, hostname, port, user_name, password, database):
        """
        Get the postgres database connection
        Args:
                hostname    (Str)  -- Hostname of client
                port        (str)  -- Port number of postgres server
                user_name   (str)  -- Username of postgres server
                password    (str)  -- Password of postgres server
                database    (str)  -- Database name
            Returns:
                Postgres database connection object
        """
        return self._get_postgres_database_connection(
            hostname,
            port,
            user_name,
            password,
            database)


class PostgresCusterHelper(PostgresHelper):
    """Helper class to perform Postgres Cluster operations"""
    def __init__(self, commcell, client, instance):
        """
        Initialize the PostgresHelper object.
            Args:
                commcell             (obj)  --  Commcell object
                client               (obj)  --  Client object
                instance             (obj)  --  Postgres CLuster instance object
        """
        self._commcell = commcell
        self._csdb = database_helper.get_csdb()
        self.log = logger.get_log()
        self._client = client
        self._instance = instance
        self.nodes = self.get_node_priority()
        self.node_data = self.get_node_data()
        self.master_node = self.get_master_node()

    def get_node_priority(self):
        """
        Returns the priority order of postgres clusters
        in the form of a python dict
        """
        try:
            query = ("SELECT name, subq.priority FROM APP_Client "
                     "JOIN APP_DBClusterInstance ON APP_Client.id = APP_DBClusterInstance.clientId "
                     "JOIN (SELECT componentNameId, attrVal AS priority "
                     "FROM APP_DBClusterInstanceProp WHERE componentNameId IN ("
                     "SELECT id FROM APP_DBClusterInstance WHERE instanceId IN ("
                     "SELECT DISTINCT instance FROM APP_Application WHERE clientId = ("
                     "SELECT id FROM app_client WHERE name = '{0}'))) "
                     "AND attrName LIKE '%Node%' AND created = (SELECT MAX(created) "
                     "FROM APP_DBClusterInstanceProp AS sub "
                     "WHERE sub.componentNameId = APP_DBClusterInstanceProp.componentNameId "
                     "AND sub.attrName LIKE '%Node%')) AS subq ON subq.componentNameId = APP_DBClusterInstance.id"
                     .format(self._client.client_name))

            self._csdb.execute(query)
            cur = self._csdb.fetch_all_rows()
            order = {}
            for server_name, priority in cur:
                order[priority] = server_name

            self.log.info("Node priority fetched successfully: %s", order)
            return order
        except Exception as e:
            self.log.error("Error fetching node priority: %s", str(e))
            raise

    def get_master_node(self):
        """
        Fetches the master node from the commcell using pg_is_in_recovery and accordingly updating priority dictionary.

        Returns:
            client name for the master node of the cluster

        Raises:
            Exception: If there is an error in fetching the master node.
        """
        try:
            nodes_order = self.nodes
            nodes_data = self.node_data
            master = None

            for node_ in nodes_order.values():
                postgres_database_object = database_helper.PostgreSQL(
                    host=self._commcell.clients.get(node_).client_hostname,
                    port=nodes_data[node_]["port"],
                    password=nodes_data[node_]["sa_password"],
                    user=nodes_data[node_]["sa_user"],
                    database="postgres"
                )
                query = "select pg_is_in_recovery();"
                result = postgres_database_object.execute(query)

                if result and not result.rows[0][0]:
                    master = node_
                    break
            if master is None:
                raise ValueError("Master node not found")
            key_to_shift = None
            for key, value in nodes_order.items():
                if value == master:
                    key_to_shift = key
                    break

            if key_to_shift is None:
                raise ValueError("Master node key not found in nodes_order")
            del nodes_order[key_to_shift]
            new_order = {"0": master}
            for i, (key, value) in enumerate(nodes_order.items(), start=1):
                new_order[str(i)] = value

            self.nodes = new_order
            return master

        except Exception as e:
            self.log.error("Error fetching master node: %s", str(e))
            raise

    def get_node_data(self):
        """
        Fetches node data from the commcell database.

        Returns:
            dict: A dictionary containing node data.

        Raises:
            Exception: If there is an error in fetching node data.
        """
        try:
            query = (
                "SELECT APP_Client.name, "
                "subq.port, subq.data_file_path, subq.binary_file_path, "
                "subq.credId, subq.config_file, "
                "subq.unix_user, subq.data_dir, subq.wal_log_index_file "
                "FROM APP_Client "
                "JOIN APP_DBClusterInstance ON APP_Client.id = APP_DBClusterInstance.clientId "
                "JOIN (SELECT APP_DBClusterInstance.id AS componentNameId, "
                "MAX(CASE WHEN APP_DBClusterInstanceProp.attrName = 'PostgreSQL Port' THEN "
                "APP_DBClusterInstanceProp.attrVal END) AS port, "
                "MAX(CASE WHEN APP_DBClusterInstanceProp.attrName = 'PostgreSQL data file path' THEN "
                "APP_DBClusterInstanceProp.attrVal END) AS data_file_path, "
                "MAX(CASE WHEN APP_DBClusterInstanceProp.attrName = 'PostgreSQL binary file path' THEN "
                "APP_DBClusterInstanceProp.attrVal END) AS binary_file_path, "
                "MAX(CASE WHEN APP_DBClusterInstanceProp.attrName = 'Credential Association Id' THEN "
                "APP_DBClusterInstanceProp.attrVal END) AS credId, "
                "MAX(CASE WHEN APP_DBClusterInstanceProp.attrName = 'PosgreSQL config file' THEN "
                "APP_DBClusterInstanceProp.attrVal END) AS config_file, "
                "MAX(CASE WHEN APP_DBClusterInstanceProp.attrName = 'PostgreSQL Unix user' THEN "
                "APP_DBClusterInstanceProp.attrVal END) AS unix_user, "
                "MAX(CASE WHEN APP_DBClusterInstanceProp.attrName = 'datadir' THEN "
                "APP_DBClusterInstanceProp.attrVal END) AS data_dir, "
                "MAX(CASE WHEN APP_DBClusterInstanceProp.attrName = 'PostgreSQL write ahead archive log index file' THEN "
                "APP_DBClusterInstanceProp.attrVal END) AS wal_log_index_file "
                "FROM APP_DBClusterInstance JOIN APP_DBClusterInstanceProp "
                "ON APP_DBClusterInstance.id = APP_DBClusterInstanceProp.componentNameId "
                "WHERE APP_DBClusterInstance.instanceId IN ("
                "SELECT DISTINCT instance FROM APP_Application "
                "WHERE clientId = (SELECT id FROM app_client WHERE name = '{0}')) "
                "GROUP BY APP_DBClusterInstance.id) AS subq ON subq.componentNameId = APP_DBClusterInstance.id".format(
                    self._client.client_name))

            self._csdb.execute(query)
            cur = self._csdb.fetch_all_rows()
            
            cred_id = cur[0][4]
            cred_query = ("select userName, password from APP_Credentials where credentialId"
                          "= (select credentialId from APP_CredentialAssoc where assocId = '{0}')".format(cred_id))
            self._csdb.execute(cred_query)
            creds = self._csdb.fetch_all_rows()
            
            data = {}
            for item in cur:
                name = item[0]
                data[name] = {
                    'port': item[1],
                    'lib_file_path': item[2],
                    'binary_file_path': item[3],
                    'sa_user': creds[0][0],
                    'config_file': item[5],
                    'sa_password': cvhelper.format_string(self._commcell, creds[0][1]),
                    'unix_user': item[6],
                    'data_dir': item[7],
                    'wal_log_index_file': item[8]
                }

            self.log.info("Node data fetched successfully: %s", data)
            return data
        except Exception as e:
            self.log.error("Error fetching node data: %s", str(e))
            raise

    def is_data_backup_on_standby(self, job_id):
        """
        Checks if data backup is on standby node.

        Args:
            job_id (str): The job ID to check.

        Returns:
            bool: True if backup is on standby, False otherwise.

        Raises:
            Exception: If there is an error executing the command.
        """
        try:
            p_node = self.nodes['1']
            priority_node = self._commcell.clients.get(p_node)
            log_path = priority_node.log_directory
            lin_machine_object = machine.Machine(
                priority_node, self._commcell)
            log_path = lin_machine_object.join_path(log_path, 'PostGresBackupParent.log')
            command = f"cat {log_path} | grep {job_id} | grep 'This is backup from Standby.'"
            output = lin_machine_object.execute_command(command)
            if output.exception_message != '':
                self.log.error("Error executing command on client machine: %s", output.exception_message)
                raise Exception("Unable to run the command on client machine")
            if str(job_id) in output.formatted_output:
                self.log.info("Data backup found on standby for job id %s", job_id)
                return True
            self.log.info("Data backup not found on standby for job id %s", job_id)
            return False
        except Exception as e:
            self.log.error("Error checking data backup on standby: %s", str(e))
            raise

    def is_log_backup_on(self, nodetype, job_id):
        """
        Checks if log backup is on the specified node type.

        Args:
            nodetype (str): The type of node ('master' or 'standby').
            job_id (str): The job ID to check.

        Returns:
            bool: True if log backup is found, False otherwise.

        Raises:
            Exception: If there is an error executing the command.
        """
        try:
            if nodetype == 'master':
                node = self._commcell.clients.get(self.master_node)
            else:
                node = self._commcell.clients.get(self.get_node_priority()['1'])
            log_path = node.log_directory
            lin_machine_object = machine.Machine(
                node, self._commcell)
            log_path = lin_machine_object.join_path(log_path, 'PostGresLogBackupParent.log')
            command = f"cat {log_path} | grep {job_id} | grep 'lBackupBase::getCollectFileAttrib'"
            output = lin_machine_object.execute_command(command)
            if output.exception_message != '':
                self.log.error("Error executing command on client machine: %s", output.exception_message)
                raise Exception("Unable to run the command on client machine")
            if str(job_id) in output.formatted_output:
                self.log.info(f"Log backup found on {nodetype} for job id %s", job_id)
                return True
            self.log.info(f"Log backup not found on {nodetype} for job id %s", job_id)
            return False
        except Exception as e:
            self.log.error(f"Error checking log backup on {nodetype}: %s", str(e))
            raise

    def validate_log_delete(self, cluster_node):
        """
        Validates the deletion of log files in the specified cluster node.

        Args:
            cluster_node (str): The name of the cluster node to check.

        Returns:
            bool: True if log files are successfully deleted, False otherwise.

        Raises:
            Exception: If there is an error in validating log deletion.
        """
        try:
            node_data = self.node_data
            log_directory = node_data[cluster_node]['wal_log_index_file']
            lin_machine_object = machine.Machine(cluster_node, self._commcell)
            command = f'find {log_directory} -type f \\( -name "*."\\) -exec ls -l {{}} +'
            output = lin_machine_object.execute_command(command)
            if output.formatted_output == '':
                self.log.info("Log files successfully deleted in directory %s", log_directory)
                return True
            self.log.info("Log files not deleted in directory %s", log_directory)
            return False
        except Exception as e:
            self.log.error("Error validating log delete: %s", str(e))
            raise

    def update_conf_file(self, node, attribute_name, value):
        """
        Updates the configuration file on the master node.

        Args:
            node (Client) : client object of node where file needs to be updated
            attribute_name (str): The name of the attribute to update.
            value (str): The new value for the attribute.

        Raises:
            Exception: If there is an error in updating the configuration file.
        """
        try:
            node = self._commcell.clients.get(node)
            node_data = self.node_data
            data_dir = node_data[node.client_name]['data_dir']
            lin_machine_object = machine.Machine(node, self._commcell)
            command = f'cd {data_dir} && sed -i "s/^{attribute_name}\s*=.*/{attribute_name} = {value}/" postgresql.conf'
            lin_machine_object.execute_command(command)
            self.log.info("Configuration file updated successfully: %s = %s", attribute_name, value)
        except Exception as e:
            self.log.error("Error updating configuration file: %s", str(e))
            raise


