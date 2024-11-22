# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing MYSQL operations

MYSQLHelper is the only class defined in this file

MYSQLHelper: Helper class to perform MYSQL operations

MYSQLHelper:
============
    __init__()                          --  initializes MYSQLHelper object

    get_mysql_db_password()             --  Gets the password of the mysql instance

    get_mysql_port()                    --  Method to get the mysql port from client

    get_database_information()          --  Method to get the database information

    get_default_subclient_contents()    --  Method to get default subclient contents

    validate_db_info()                  --  Method to validate database information

    drop_table()                        --  Method to drop a table from database

    clean_up_tables()                   --  This Function takes a dictionary as input.
    The dictionary has the database names as keys and table names list as values.
    This function calls the drop_table()

    cleanup_database_contents()         --  method to clean all views and tables in database

    basic_setup_on_mysql_server()       --  This function checks for basic settings on MYSQL Server

    get_tables_list_for_db()            --  This function get list of tables for given DataBases

    get_table_size()                    --  Method to get the table name and number of rows
    for all the tables under given database

    log_bin_on_mysql_server()           --  This function checks whether LOG_BIN ON or OFF,
    If its OFF then incremental(Log) backup cannot be run.

    create_table_with_text_db()         --  This function created the table with the
    given name as prefix and inserts data

    create_view()                       --  Creates a view inside a database

    drop_view()                         --  Drops a view inside a database

    list_views()                        --  Lists views inside a database

    generate_test_data()                --  Function to generate test data for the automation
    purpose. Adds specified number of Databases, tables and Rows with a specified Prefix

    cleanup_test_data()                 --  Cleans up test data which are generated for automation

    start_mysql_server()                --  Starts the mysql server in client

    stop_mysql_server()                 --  Stops the mysql server in client

    get_server_status()                 --  Gets the status of mysql server

    run_restore()                       --  Initiates the restore job for the specified subclient

    snap_blocklevel_testcase()          --  Method to perform backup/restore and validation of
    snap and block level feature TCs

    snap_prerequirement_check()         --  Method to check if the pre requirement to
    run snap/block level testcase is met or not

    blocklevel_redirect_restore()       --  Method to perform redirect restore testcase for
    snap and block level cases

    _redirect_operations()              --  Method to perform operations related to redirect restore

    innodb_file_per_table()             --  Checks if the innodb_files_per_table is enabled
    in the server or not

    is_xtrabackup_eligible()            --  Checks if the server is eligible to run xtrabackup

    is_xtrabackup_effective()           --  Method to check if the xtrabackup is being
    used for the backup

    backup_job_ran_on()                 --  Method to get the client and instance details on
    which backup job was run

    populate_database()                 --  Inserts test tables and views in the each
    database in the subclient content

    run_proxy_backup()                  --  Initiates the backup job on proxy subclient and
    checks if the proxy is honored

    proxy_testcase()                    --  Method to run proxy testcases

    _get_mysql_database_connection()    --  Method for database connection

    run_data_restore_and_validation()   --  Method to run Data only restore

    delete_table_for_dependent_views()  --  Method to delete first two tables having dependent
    views from the database list

    get_job_event_description_with_severity_six()   --  Method to gets the events from job
    description having severity as 6

    get_sbt_image_for_meb_operation()   --  Method to get sbt image name for meb operation from
    client machine logs

    check_comments_in_table()           --  Method to verify comment string in create table command

    verify_no_lock_parameter_in_meb_command()   --  Method to verify no locking parameters in
    MySQL Enterprise backup command

    verify_meb_properties_on_instance() --  Method to verify if MEB is enabled, set the MEB bin
    path on source MySQL Instance

    run_meb_backup_flow()               --  Method to run the backup flow (one full backup
    followed by two incremental backups) for MySQL Enterprise Backup functionality

    run_meb_restore_flow()              --  Method to run browse and restore from second
    incremental MEB backup

    validate_meb_data_and_image()       --  Method to validate meb data and sbt image after MEB
    restore operation

    fetch_mysql_variant_name_from_version()     --  Method to get the mysql variant name from
    mysqld --version command

    acceptance_test_case_traditional()  --  Method to execute acceptance test for MySQL
    iDA traditional for various mysql variants

    check_table_engine()                --  Validate table engine in a database is same as expected

MYSQLHelper Instance Attributes:
================================
    **data_directory**                  --  returns mysql data directory

    **partition_enabled**               --  returns true if the partition is enabled
    in database server

"""

import string
import os
import time
import re
from AutomationUtils import logger
from AutomationUtils import machine
from AutomationUtils import constants
from AutomationUtils import cvhelper
from AutomationUtils import database_helper
from Database.dbhelper import DbHelper
from Application.CloudApps.azure_helper import AzureAuthToken


class MYSQLHelper(object):
    """Helper class to perform mysql operations"""

    def __init__(self, commcell, subclient=None, instance=None, hostname=None, user=None, port=None,
                 connection_info=None, ssl_ca=None, ssl_cert=None, ssl_key=None, is_mi=False, backup_gateway=None):
        """Initializes mysqlhelper object

        Args:
                commcell             (obj)  --  Commcell object

                subclient            (obj)  --  Subclient Object

                        default: None

                instance             (obj)  --  Instance object

                        default: None

                hostname             (str)  --  Cient hostname

                        default: None

                user                 (str)  --  MySQL server username

                        default: None

                port                 (int)  --  MySQL server port number

                    default: None

                connection_info      (dict) --  dictoinary containing connection information
                that needs to be provided only if subclient and instance objects are not provided

                    default: None

                    Format:
                        connection_info = {
                            'client_name': 'client_name',
                            'instance_name':'instance_name',
                            'socket_file':'socket_file/port(incase of windows)'}
                ssl_ca              (str) -- SSL CA path Location on the access node

                is_mi                (bool) -- True , if managed identity based authentication

                backup_gateway      (str) -- backup_gateway name

            Returns:
                object - instance of this class

        """

        self.commcell = commcell
        # self.csdb = database_helper.get_csdb()
        self.csdb = database_helper.CommServDatabase(self.commcell)
        self.log = logger.get_log()
        self.subclient = None
        self.mysql_instance = None
        self.pwd = None
        self.client = None
        self.machine_object = None
        self.port = port
        self.db_connect = None
        self.bin_dir = None
        self._mysql_client_name = None
        self._mysql_instance_name = None
        self.socket_file = None
        self.mysql_db_connection_object = None
        self.is_cloud_db = False
        self.mysql_port = None
        self.host_name = hostname
        self.ssl_ca = ssl_ca
        self.ssl_key = ssl_key
        self.ssl_cert = ssl_cert
        self._ad_auth_mi = is_mi
        self.backup_gateway = backup_gateway

        if str(self.port).find(":") >= 0:
            self.is_cloud_db = True
            self.mysql_port = int(self.port.split(":")[1])
            mysql_server_name = self.port.split(":")[0]
            self.host_name = mysql_server_name

        if subclient and instance:
            self.subclient = subclient
            self.mysql_instance = instance
            if self.is_cloud_db != True:
                self.client = self.mysql_instance._agent_object._client_object
                self.machine_object = machine.Machine(self.client)
                self.bin_dir = self.mysql_instance.binary_directory.rstrip("/")
                self.socket_file = self.mysql_instance.port
        else:
            self._mysql_client_name = connection_info['client_name']
            self._mysql_instance_name = connection_info['instance_name']
            self.get_mysql_bin_dir(self._mysql_client_name, self._mysql_instance_name)
            self.machine_object = machine.Machine(self._mysql_client_name, self.commcell)
            self.socket_file = connection_info['socket_file']

        self.pwd = self.get_mysql_db_password()
        self.usr = user

        self.data = {
            'BINDIR': self.bin_dir,
            'USERNAME': self.usr,
            'PASSWORD': self.pwd,
            'SOCKFILE': self.socket_file
            }
        self.dbhelper_object = None
        self._data_directory = None
        self._partition_enabled = None


        if self.is_cloud_db != True:
            if "windows" in self.machine_object.os_info.lower():
                self.port = int(self.socket_file)
        self.get_mysql_port()
        self.mysql_db_connection_object = self._get_mysql_database_connection()

    @property
    def data_directory(self):
        """returns mysql data directory

        Returns:
            (str)   --  MySQL data directory

        """
        if not self._data_directory:
            output = database_helper.MySQL(
                self.host_name, self.usr, self.pwd, self.port).execute(
                    "SHOW VARIABLES WHERE Variable_Name LIKE 'datadir';")
            self._data_directory = output.rows[0][1].rstrip(
                self.machine_object.os_sep)
        return self._data_directory

    @property
    def partition_enabled(self):
        """returns true if the partition is enabled in database server

        Returns:

            (bool)  --  True if partition is enabled
                        False if partition not enabled

        """
        if self._partition_enabled is None:
            output = self.mysql_db_connection_object.execute(
                    "SELECT PLUGIN_STATUS FROM INFORMATION_SCHEMA.PLUGINS "
                    "where PLUGIN_NAME='partition';")
            if not output.rows:
                self._partition_enabled = False
            else:
                self._partition_enabled = output.rows[0][0].lower() == "active"
        return self._partition_enabled

    def get_mysql_bin_dir(
            self,
            client_name,
            instance_name):
        """ Gets mysql binary directory
        Args:

            client_name        (str)    -- client name

            instance_name      (str)    -- Mysql instance name

        """

        query = (
            "select attrVal from APP_InstanceProp where componentNameId=(select distinct "
            "instance from APP_Application where clientId=(select id from APP_Client "
            "where name='{0}') and instance in (select id from APP_InstanceName where "
            "name='{1}')) and attrName='MySQL binary file path'".format(client_name, instance_name))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()

        if cur:
            self.log.info("Bin directory of MySQL instance is fetched Successfully")
            self.bin_dir = cur[0].rstrip('/')
        else:
            raise Exception("Failed to get the MySQL instance bin directory")

    def get_mysql_db_password(self):
        """Gets the password of the mysql instance

        Returns:

            mysql_db_password   (str)   --  Password of mysql server

        Raises:

            Exception:
                if failed to get the password of the instance

        """

        try:
            if self.mysql_instance:
                query = "Select attrVal from APP_InstanceProp where componentNameId = {0} and \
                        attrName = 'MySQL Use AD Authentication'".format(self.mysql_instance.instance_id)
                self.csdb.execute(query)
                flag = self.csdb.fetch_one_row()
                ad_auth = flag[0]
                if len(ad_auth) != 0 and int(ad_auth) == 1:
                    azure_mysql_app_token_object = AzureAuthToken()
                    if self._ad_auth_mi:
                        mysql_db_password = azure_mysql_app_token_object.generate_auth_token_mi_ad_auth(
                            self.backup_gateway, self.commcell)
                        return mysql_db_password
                    else:
                        mysql_db_password = azure_mysql_app_token_object.generate_auth_token_iam_ad_auth()
                        return mysql_db_password
                else:
                    query = "Select attrVal from app_instanceprop where componentNameId = {0} and \
                        attrName = 'MySQL SA Password'".format(self.mysql_instance.instance_id)
            else:
                query = (
                    "Select attrVal from app_instanceprop where componentNameId = "
                    "(select distinct instance from APP_Application where instance in "
                    "(select id from APP_InstanceName where name='{1}') and clientId="
                    "(select id from app_client where name='{0}')) and "
                    "attrName = 'MySQL SA password'".format(
                        self._mysql_client_name, self._mysql_instance_name))
            self.csdb.execute(query)
            password = self.csdb.fetch_one_row()
            password = password[0]
            mysql_db_password = cvhelper.format_string(self.commcell, password)
            return mysql_db_password
        except Exception:
            raise Exception("Could not get the mysql server password. ")

    def get_mysql_port(self):
        """ method to get the mysql port from client

        Returns:

            (int)   --  MySQL Port number

        Raises:

            Exception:

                if fails to get the port

        """
        if self.port:
            return self.port
        if "windows" in self.machine_object.os_info.lower():
            self.port = int(self.mysql_instance.port)
            return self.port
        if self.get_server_status():
            self.log.info("Getting the MySQL port")
            self.data['OPERATION'] = 'port'

            output = self.machine_object.execute_script(
                constants.UNIX_MYSQL_SERVER_OPERATIONS,
                self.data)

            if output.exception_message:
                raise Exception(output.exception_message)
            elif output.exception:
                raise Exception(output.exception)
            self.port = int(output.formatted_output)
            return self.port
        else:
            raise Exception("Server is not running, cannot get the port Number")

    def get_database_information(self, database_list=None):
        """ method to get the database information

        Args:

            database_list     (list)  -- Database list

        Returns:

            db_info_dict      (dict)  --  Dictionary including database information

        Raises:

            Exception:
                if unable to generate db information

        """
        self.mysql_db_connection_object = self._get_mysql_database_connection()
        if database_list is None:
            database_list = self.mysql_db_connection_object.get_db_list()
            self.mysql_db_connection_object.close()
        db_info_dict = dict()
        try:
            for database in database_list:
                table_info_map = None
                if database.startswith('\\'):
                    database = database.lstrip("\\")
                else:
                    database = database.lstrip('/')

                if database in ['mysql', 'sys', 'information_schema', 'performance_schema', 'aria_log_control']:
                    continue
                else:
                    table_info_map = self.get_table_size(
                        database)
                    db_info_dict[database] = table_info_map
            return db_info_dict
        except Exception:
            raise Exception("Unable to generate db information")

    def get_default_subclient_contents(self):
        """Method to get default subclient contents"""
        self.log.info("Default Subclient:%s", self.subclient.subclient_name)
        backupset_object = self.subclient._backupset_object
        subclient_list = list(backupset_object.subclients.all_subclients.keys())
        default_subclient = backupset_object.subclients.default_subclient
        if self.subclient.subclient_name.lower() != default_subclient.lower():
            return
        database_list = self.mysql_db_connection_object.get_db_list()
        all_other_sub_clients_contents = list()
        for subclient in subclient_list:
            if subclient == "(command line)":
                continue
            if subclient.lower() != default_subclient.lower():
                self.log.info("Subclient is not default subclient")
                sub_client_new = backupset_object.subclients.get(subclient)
                self.log.info("Subc: %s and content: %s", subclient, sub_client_new.content)
                for database in sub_client_new.content:
                    all_other_sub_clients_contents.append(
                        database)
        self.log.info("All other subc content: %s", all_other_sub_clients_contents)
        if "windows" in self.client.os_info.lower():
            database_list = ["\\{0}".format(element) for element in database_list]
            system_databases = ["\\performance_schema", "\\information_schema"]
        else:
            database_list = ["/{0}".format(element) for element in database_list]
            system_databases = ["/performance_schema", "/information_schema"]
        database_list = [element for element in database_list if element not in system_databases]
        for db_name in all_other_sub_clients_contents:
            if db_name.strip in database_list:
                database_list.remove(db_name)
        self.subclient.content = database_list
        return

    def validate_db_info(
            self,
            database_info_1,
            database_info_2):
        """Method to validate database information

        Args:

            database_info_1     (dict)  -- information of first database

            database_info_2     (dict)  -- information of second database

        Raises:

            Exception:
                if database validations fails

        """

        if database_info_1 == database_info_2:
            self.log.info("####Database Information validation success####")
            return
        self.log.info("DB1:%s", database_info_1)
        self.log.info("DB2:%s", database_info_2)
        raise Exception("Database Information validation failed..!!")

    def drop_table(self, database_name, table_name):
        """ Method to drop a table from database

        Args:

            database_name     (str)  -- Name of the database

            table_name        (str)  -- Name of the table to drop

        Raises:

            Exception:
                if unable to drop the table

        """

        if database_name.startswith('\\'):
            db_name = database_name.lstrip("\\")
            tb_name = table_name.lstrip("\\")
        else:
            db_name = database_name.lstrip("/")
            tb_name = table_name.lstrip("/")

        try:
            self.mysql_db_connection_object = self._get_mysql_database_connection(database=db_name)
            cmd = "drop table IF EXISTS `{0}`;".format(tb_name)
            self.mysql_db_connection_object.execute(cmd)

        except Exception:
            raise Exception("Could not drop the table. ")

    def clean_up_tables(self, tables_dict):
        """ This Function takes a dictionary as input.
            The dictionary has the database names as keys and table names list as values.
            This function calls the drop_table()

        Args:

            tables_dict     (dict)  -- Dictionary of database and tables

                Accepted format: {
                                    "database1": ["tab1", "tab2"],
                                    "database2": ["tab1", "tab2"],
                                    "database3": ["tab1", "tab2"]

                                 }

        """
        for each_db in tables_dict:
            table_list = tables_dict[each_db]
            self.log.info("Cleaning tables:%s from DB:%s:", table_list, each_db)
            for each_table in table_list:
                self.drop_table(each_db, each_table)

    def cleanup_database_contents(self, database_list=None, subclient_content=None):
        """method to clean all views and tables in database

        Args:

            database_list     (list)  -- list of databases

                default: None

            subclient_content (list)  -- list of databases in subclient content

                default: None

        """
        if database_list is None:
            if not subclient_content and not self.subclient:
                raise Exception("Subclient content or database list needs to passed to the method")
            if self.subclient:
                subclient_content = self.subclient.content
            self.log.info(
                "Database list is NONE, deleting tables in all "
                "the databases specified in the subclient content.")
            contents = subclient_content
            contents = [database.strip("/") for database in contents]
            contents = [database.strip("\\") for database in contents]
            dblist = contents.copy()
            for database in dblist:
                if database in ['mysql', 'sys', 'aria_log_control']:
                    contents.remove(database)
            database_list = contents

        for database in database_list:
            table_list = self.get_tables_list_for_db(database)
            view_list = self.list_views(database)
            for table in table_list:
                self.drop_table(database, table)
            for view in view_list:
                self.drop_view(view, database)
        self.log.info("Tables and views in all the databases are dropped")


    def basic_setup_on_mysql_server(self, log_bin_check=False):
        """ This function checks for basic settings on MYSQL Server

        Args:
            log_bin_check   (bool)   -- boolean value to specify if
            log bin value needs to be checked on server or not

        Raises:

            Exception:
                if unable verify basic setup on mysql server

        """
        auto_path = os.path.dirname(os.path.dirname(__file__))
        image_file = os.path.join(auto_path, "MySQLUtils", "SampleImage.wmf")
        try:
            self.log.info("Getting the size of file: %s ", image_file)
            image_file_size = os.path.getsize(image_file)
            self.log.info("Checking for max_allowed Packets for the Blob type data base")
            cmd = "show variables like 'max_allowed_packet';"
            self.log.info("Excecuting the command: %s to get max_allowed Packets", cmd)
            output = self.mysql_db_connection_object.execute(cmd)
            max_size = int(output.rows[0][1])
            self.log.info("Output: %s", str(max_size))
            if max_size > image_file_size:
                pass
            else:
                self.log.info(
                    "The Input Image size: %s is greater than "
                    "max_allowed_packet size: %s", image_file_size, max_size)
            if log_bin_check:
                self.log_bin_on_mysql_server()

        except Exception:
            raise Exception("Exception raised at basic_setup_on_mysql_server. ")

    def get_tables_list_for_db(self, database_name):
        """ This function get list of tables for given DataBases

        Args:

            database_name     (str)  -- Database name

        Returns:

            table_list        (list)  -- List of tables in the database

        Raises:

            Exception:
                if unable to get the table list

        """

        tables_list = []
        db_name = database_name
        try:
            self.log.info("Get List of tables in database:%s", db_name)
            self.mysql_db_connection_object = self._get_mysql_database_connection(database=database_name)
            query = "SHOW FULL TABLES WHERE table_type = 'BASE TABLE';"
            list_tb = self.mysql_db_connection_object.execute(query)
            list_tb = list(list_tb.rows)
            for row in list_tb:
                tables_list.append(row[0])
            return tables_list

        except Exception:
            raise Exception("Could not get the table list. ")

    def get_table_size(self, database_name):
        """ method to get the table name and number of rows
        for all the tables under given database

        Args:

            database_name     (str)  -- Database name

        Returns:

            table_info_map    (dict)  -- Dictionary consisting of table name as
            Key and row count as value

        Raises:

            Exception:
                if unable get the table size

        """

        table_list = self.get_tables_list_for_db(database_name)
        table_list.extend(self.list_views(database_name))
        try:
            table_info_map = {}
            for table in table_list:
                query = "select count(*) from `%s`;" % table
                self.mysql_db_connection_object = self._get_mysql_database_connection(database=database_name)
                response = self.mysql_db_connection_object.execute(query)
                table_info_map[table] = response.rows[0][0]

            return table_info_map
        except Exception:
            raise Exception("Exception in Getting table size")

    def log_bin_on_mysql_server(self):
        """ This function checks whether LOG_BIN ON or OFF,
            If its OFF then incremental(Log) backup cannot be run.

        Returns:

            True if the LOG_BIN value is on.

        Raises:

            Exception:
                if LOG_BIN value is OFF

                if Unable to get the LOG_BIN value

        """

        try:
            self.log.info("Checking whether LOG_BIN has been Enable or Disable")
            cmd = "show variables like 'log_bin';"
            self.log.info("Excecuting the command:%s to Check LOG_BIN Properties", cmd)
            output = self.mysql_db_connection_object.execute(cmd)
            status = output.rows[0][1]
            self.log.info("Output: %s", status)
            if status == ('log_bin', 'ON'):
                pass
            elif status == ('log_bin', 'OFF'):
                raise Exception(
                    (
                        "Binary Logging disabled, Kindly enable "
                        "binary logging to run incremental backup"))
        except Exception:
            raise Exception("Unable to get the LOG_BIN value")

    def create_table_with_text_db(
            self,
            database_name,
            table_name="AutomTable",
            no_of_tables=500,
            column_in_each_table=7,
            drop_table_before_create=False,
            comment_string="",
            engine="InnoDB"):
        """This function creates the table with the given name as prefix and inserts data

        Args:

            database_name               (str)  -- Database name

            table_name                  (str)  -- Tablename prefix to create inside the database

                default: "AutomTable"

            no_of_tables                (int)  -- Number of tables to create

                default: 500

            column_in_each_table        (int)  -- Number of columns to be created

                default: 7

            drop_table_before_create    (bool) -- Flag to determine if table
            needs to be dropped if already exists

                default: False

            comment_string              (str)  -- Text to be used in comments while creating tables

                default: ""

            engine                      (str)  -- Engine to be used when creating table

                default: "InnoDB"

        Returns:

            tables_created              (list) -- List of tables created under ther given database

        Raises:

            Exception:
                if unable create tables

        """
        if database_name.startswith('\\'):
            database_name = database_name.lstrip("\\")
        else:
            database_name = database_name.lstrip("/")

        table_name = table_name
        tables_created = []
        try:
            if database_name not in ["mysql", "sys", "aria_log_control"]:
                self.log.info("Creating tables inside DB:%s", database_name)
                self.mysql_db_connection_object = self._get_mysql_database_connection(database=database_name)

                for each_table in range(0, no_of_tables):
                    each_table_name = "{0}_{1}_txtdt_{2}" .format(
                        database_name, table_name, each_table)

                    if drop_table_before_create:
                        self.drop_table(database_name,
                                        each_table_name)
                    sql_query = ""
                    if self.partition_enabled:
                        if comment_string:
                            sql_query = (
                            "CREATE TABLE IF NOT EXISTS `%s`(id int unsigned primary key "
                            "AUTO_INCREMENT COMMENT '%s',column_var CHAR(254) COMMENT '%s', "
                            "column_string VARCHAR(254),column_tinytext TINYTEXT NOT NULL, "
                            "column_text TEXT NOT NULL,column_mediumtext MEDIUMTEXT NOT NULL, "
                            "column_longtext LONGTEXT NOT NULL) PARTITION BY RANGE (id) ("
                            "PARTITION p0 VALUES LESS THAN (10), PARTITION p1 VALUES LESS THAN ("
                            "30), PARTITION p2 VALUES LESS THAN (45), PARTITION p3 VALUES LESS "
                             "THAN MAXVALUE)") % (each_table_name, comment_string, comment_string)
                        else:
                            sql_query = (
                            "CREATE TABLE IF NOT EXISTS `%s`(id int unsigned primary key "
                            "AUTO_INCREMENT,column_var CHAR(254), column_string VARCHAR(254),"
                            "column_tinytext TINYTEXT NOT NULL, column_text TEXT NOT NULL, "
                            "column_mediumtext MEDIUMTEXT NOT NULL, column_longtext LONGTEXT "
                            "NOT NULL) PARTITION BY RANGE (id) (PARTITION p0 VALUES LESS THAN "
                            "(10), PARTITION p1 VALUES LESS THAN (30), PARTITION p2 VALUES LESS"
                            " THAN (45), PARTITION p3 VALUES LESS "
                            "THAN MAXVALUE)") % (each_table_name)

                    else:
                        if comment_string:
                            sql_query = (
                            "CREATE TABLE IF NOT EXISTS `%s`(id int unsigned primary key "
                            "AUTO_INCREMENT COMMENT '%s',column_var CHAR(254) COMMENT '%s', "
                            "column_string VARCHAR(254),column_tinytext TINYTEXT NOT NULL, "
                            "column_text TEXT NOT NULL,column_mediumtext MEDIUMTEXT NOT NULL, "
                            "column_longtext LONGTEXT NOT NULL)") % (each_table_name,
                                                                     comment_string,
                                                                     comment_string)
                        else:
                            sql_query = (
                            "CREATE TABLE IF NOT EXISTS `%s`(id int unsigned primary key "
                            "AUTO_INCREMENT,column_var CHAR(254), column_string VARCHAR(254),"
                            "column_tinytext TINYTEXT NOT NULL, column_text TEXT NOT NULL,"
                            " column_mediumtext MEDIUMTEXT NOT NULL, "
                            "column_longtext LONGTEXT NOT NULL)") % (each_table_name)
                    sql_query = sql_query + f'ENGINE = {engine}'
                    self.mysql_db_connection_object = self._get_mysql_database_connection(
                        database=database_name)
                    self.mysql_db_connection_object.execute(sql_query)
                    #**************** Insert the values into the database*********************
                    sample_data_for_text_data_type = string.ascii_letters
                    number_of_columns = column_in_each_table
                    while number_of_columns > 0:
                        self.mysql_db_connection_object.execute(
                            "insert into `%s`(`id`,`column_var`, `column_string`, `column_tinytext`\
                            , `column_text`, `column_mediumtext`, `column_longtext`) values \
                            (NULL, '%s','%s','%s','%s','%s','%s')" %
                            (each_table_name,
                             sample_data_for_text_data_type,
                             sample_data_for_text_data_type,
                             sample_data_for_text_data_type,
                             sample_data_for_text_data_type,
                             sample_data_for_text_data_type,
                             sample_data_for_text_data_type))
                        number_of_columns -= 1

                    tables_created.append(each_table_name)
            self.log.info("Tables are created.")
            return tables_created

        except Exception:
            raise Exception("Exception raised at create_table_with_text_db")

    def create_view(
            self,
            query,
            view_name,
            database_name):
        """ Creates a view inside a database.

            Args:
                query               (str)  -- Query to create view

                view_name           (str)  -- Name of the view

                database_name       (str)  -- database name

            Raises:
                Exception:
                    if unable to create view
        """
        try:
            self.mysql_db_connection_object = self._get_mysql_database_connection(database=database_name)
            query = "create or replace view `{0}` as {1}".format(view_name, query)
            self.mysql_db_connection_object.execute(query)

        except Exception:
            self.log.error("Exception in creating View")
            raise Exception("Unable to create the view")

    def drop_view(self, view_name, database_name):
        """ Drops a view inside a database.

            Args:
                view_name           (str)  -- Name of the view

                database_name       (str)  -- database name

            Raises:
                Exception:
                    if unable to drop view
        """
        try:
            self.mysql_db_connection_object = self._get_mysql_database_connection(database=database_name)
            query = "drop view if exists `{0}` cascade;".format(view_name)
            self.mysql_db_connection_object.execute(query)

        except Exception:
            self.log.error("Exception in dropping View")
            raise Exception("Unable to drop the view")

    def list_views(self, database_name):
        """ Lists views inside a database.

            Args:

                database_name       (str)  -- database name

            Returns:

                (list) -- list of views in the database

            Raises:
                Exception:
                    if unable to list views
        """
        try:
            self.mysql_db_connection_object = self._get_mysql_database_connection(database=database_name)
            query = "SHOW FULL TABLES IN `{0}` WHERE TABLE_TYPE LIKE 'VIEW';".format(
                database_name)
            response_object = self.mysql_db_connection_object.execute(query)
            rows = response_object.rows
            view_list = []
            for view_name in rows:
                view_list.append(view_name[0].strip())
            return view_list

        except Exception:
            self.log.error("Exception in listing Views")
            raise Exception("Unable to list views")

    def generate_test_data(
            self,
            database_prefix="automation",
            num_of_databases=5,
            num_of_tables=10,
            num_of_rows=50,
            **kwargs):
        """ Function to generate test data for the automation purpose. Adds specified number of
        Databases, tables and Rows with a specified Prefix

        Args:
            database_prefix         (str)       -- prefix for each database created

                default: "automation"

            num_of_databases        (int)       -- Number of database to create

                default: 5

            num_of_tables           (int)       -- Number of tables to create inside each db

                default: 10

            num_of_rows             (int)       -- Number of rows in each table

                default: 50

            kwargs      (dict)  -- dict of keyword arguments as follows

                comment_string          (str)       --  Text to be used in comment while creating
                table

                    default: ""

                cross_cloud             (bool)      --  True if data generation is for cross-cloud restores

                    default: False

                engine                  (str)       -- Engine for table creation

                    default: "InnoDB"
        Returns:
            list   -- Database list created

        """
        test_db_list = []
        for each_db in range(0, num_of_databases):
            database = "{0}_testdb_{1}".format(database_prefix, each_db)
            # Check if database exists or not
            if self.mysql_db_connection_object.check_if_db_exists(database):
                self.mysql_db_connection_object.drop_db(
                    database)
            self.mysql_db_connection_object.create_db(database)
            self.log.info(
                "Creating %s MySQL database and tables in %s host on %s port with %s userName",
                database, self.host_name, self.port, self.usr)

            tables_created = self.create_table_with_text_db(
                database,
                table_name="Test_table",
                no_of_tables=num_of_tables,
                column_in_each_table=num_of_rows,
                comment_string=kwargs.get('comment_string', ""),
                engine=kwargs.get('engine', "InnoDB"))
            for table in tables_created:
                if not kwargs.get('cross_cloud', False):
                    self.create_view(
                        "select count(*) from `{0}`".format(table),
                        "TestView_{0}".format(table),
                        database)

            test_db_list.append(database)
        return test_db_list

    def cleanup_test_data(
            self,
            database_prefix):
        """
        Cleans up test data which are generated for automation

        Args:

            database_prefix     (str) -- prefix for each database to be deleted

        """
        self.mysql_db_connection_object = self._get_mysql_database_connection()
        database_list = self.mysql_db_connection_object.get_db_list()
        dbs_to_delete = []
        for database in database_list:
            if database.startswith(database_prefix):
                dbs_to_delete.append(database)
        self.log.info("Database list to delete:%s", dbs_to_delete)
        for database in dbs_to_delete:
            self.mysql_db_connection_object.drop_db(database)
        self.log.info("All the testdata is now deleted")

    def start_mysql_server(self):
        """ Starts the mysql server in client

        Raises:

            Exception:

                if server start operation fails

        """
        if not self.get_server_status():
            self.log.info("Starting the server")
            if not self.machine_object.check_registry_exists("MySQL", "sServerStartCmd"):
                raise Exception("Please set REGKEY: 'sServerStartCmd' on client")
            start_command = self.machine_object.get_registry_value(
                "MySQL", "sServerStartCmd")
            if "windows" not in self.machine_object.os_info.lower():
                start_command = "{0} 2> /dev/null".format(start_command)
            output = self.machine_object.execute_command(start_command)

            if output.exception_message:
                raise Exception(output.exception_message)
            elif output.exception:
                raise Exception(output.exception)
            self.log.info("sleeping for 5 seconds before checking server status")
            time.sleep(5)
            if not self.get_server_status():
                raise Exception("Unable to start the server")
            self.log.debug("Output of MySQL server start script: %s", output.formatted_output)
            self.log.info("Successfully started the MySQL Server")
        else:
            self.log.info("Server is already started")

    def stop_mysql_server(self):
        """ Stops the mysql server in client

        Raises:

            Exception:

                if server stop operation fails

        """
        if self.get_server_status():
            self.log.info("Stopping the server")
            self.data['OPERATION'] = 'shutdown'

            if "unix" in self.machine_object.os_info.lower():
                output = self.machine_object.execute_script(
                    constants.UNIX_MYSQL_SERVER_OPERATIONS,
                    self.data)
            else:
                output = self.machine_object.execute_script(
                    constants.WINDOWS_MYSQL_SERVER_OPERATIONS,
                    self.data)
            if output.exception_message:
                raise Exception(output.exception_message)
            elif output.exception:
                raise Exception(output.exception)
            self.log.info("sleeping for 5 seconds before checking server status")
            time.sleep(5)
            if self.get_server_status():
                raise Exception("Unable to stop the server")
            self.log.debug("Output of MySQL server stop script: %s", output.formatted_output)
            self.log.info("Successfully Stopped the MySQL Server")
        else:
            self.log.info("Server is already stopped")

    def get_server_status(self):
        """ gets the status of mysql server

        Returns:

            (bool)  --  True if MySQL server is running
                        False if MySQL server is not running

        Raises:

            Exception:

                if unable to fetch server status

        """
        self.log.info("Getting the Server status")
        self.data['OPERATION'] = 'status'

        if "unix" in self.machine_object.os_info.lower():
            output = self.machine_object.execute_script(
                constants.UNIX_MYSQL_SERVER_OPERATIONS,
                self.data)
        else:
            output = self.machine_object.execute_script(
                constants.WINDOWS_MYSQL_SERVER_OPERATIONS,
                self.data)
        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)
        if output.formatted_output == '':
            return False
        return True

    def run_restore(
            self,
            db_list,
            copy_precedence=None,
            table_level_restore=False,
            clone_env=False,
            clone_options=None,
            redirect_path=None, destination_client_name=None, destination_instance_name=None):
        """Initiates the restore job for the specified subclient

        Args:

            db_list                     (list)   -- List of databases to restore

            copy_precedence             (int)    -- Copy precedence number

                default: None

            table_level_restore         (bool)   -- Table level restore flag

                default: False

            clone_env                   (bool)  --  boolean to specify whether the database
            should be cloned or not

                default: False

            clone_options               (dict)  --  clone restore options passed in a dict

                default: None

                Accepted format: {
                                    "stagingLocaion": "/gk_snap",
                                    "forceCleanup": True,
                                    "port": "5595",
                                    "libDirectory": "",
                                    "isInstanceSelected": True,
                                    "reservationPeriodS": 3600,
                                    "user": "",
                                    "binaryDirectory": "/usr/bin"

                                 }

            redirect_path               (str)   --  Path specified in advanced restore options
            in order to perform redirect restore

                default: None

            destination_client_name     (str)   --  Destination client name

                defsult: None

            destination_instance_name   (str)   --  Destination instance name

                default: None

        Returns:

            (obj)   -- returns restore JOB object

        Raises:

            Exception           --  if restore job fails to run

        """
        redirect_enabled = False
        if not destination_client_name:
            destination_client_name = self.client.client_name
        if not destination_instance_name:
            destination_instance_name = self.mysql_instance.instance_name
        if redirect_path:
            redirect_enabled = True
        job = self.subclient.restore_in_place(
            db_list,
            self.client.job_results_directory,
            destination_client_name,
            destination_instance_name,
            log_restore=True,
            media_agent=self.client.client_name,
            copy_precedence=copy_precedence,
            table_level_restore=table_level_restore,
            clone_env=clone_env,
            clone_options=clone_options,
            redirect_enabled=redirect_enabled,
            redirect_path=redirect_path)
        self.log.info(
            "####Started Restore with Job ID: %s####", job.job_id)
        if not job.wait_for_completion():
            raise Exception("Failed to run restore job with error:{0}".format(job.delay_reason))
        self.log.info("Successfully finished restore job")
        return job

    def snap_blocklevel_testcase(self, testcase_type="ACC1"):
        """method to perform backup/restore and validation of snap and
        block level feature TCs

        Args:

                testcase_type       (str)   --  testcase type

                    default: None

                    Accepted values: ACC1/INCREMENTAL/SYNTH_FULL/POINT_IN_TIME

        """
        if self.dbhelper_object is None:
            self.dbhelper_object = DbHelper(self.commcell)
        # Checking the basic settings required for Automation
        self.log.info(
            "Check Basic Setting of mysql server before stating the test cases")
        self.basic_setup_on_mysql_server()

        # populate test data
        self.generate_test_data()
        self.log.info("Test Data generated..!!")

        ###################### Running Full Backup ########################
        self.log.info("Starting FULL backup job")
        full_job = self.dbhelper_object.run_backup(self.subclient, "FULL")

        full_job_log = self.dbhelper_object.get_snap_log_backup_job(full_job.job_id)
        self.log.info("Log backup job with ID:%s is now completed", full_job_log.job_id)

        if "native" in self.subclient.snapshot_engine_name.lower():
            self.log.info(
                (
                    "Native Snap engine is being run. Backup "
                    "copy job will run inline to snap backup"))
            self.log.info("Getting the backup job ID of backup copy job")
            job = self.dbhelper_object.get_backup_copy_job(full_job.job_id)
            self.log.info("Job ID of backup copy Job is: %s", job.job_id)

        self.generate_test_data("automation_inc", 2, 3, 50)
        self.log.info("Test Data generated before Incremental..!!")

        # run incremental backup
        self.log.info("Starting Incremental backup job")
        inc_job = self.dbhelper_object.run_backup(
            self.subclient, "Incremental", inc_with_data=True)
        # Wait for log backup to complete
        inc_job_log = self.dbhelper_object.get_snap_log_backup_job(inc_job.job_id)
        self.log.info("Log backup job with ID:%s is now completed", inc_job_log.job_id)

        if "native" in self.subclient.snapshot_engine_name.lower():
            self.log.info(
                (
                    "Native Snap engine is being run. Backup "
                    "copy job will run inline to snap backup"))
            self.log.info("Getting the backup job ID of backup copy job")
            job = self.dbhelper_object.get_backup_copy_job(inc_job.job_id)
            self.log.info("Job ID of backup copy Job is: %s", job.job_id)

        else:
            if "synth_full" not in testcase_type.lower():
                db_size_before = self.get_database_information()
                self.stop_mysql_server()
                # Restore from Snap copy
                self.run_restore(["/"])
                db_size_after = self.get_database_information()
                self.validate_db_info(
                    db_size_before, db_size_after)
            self.log.info(
                "Running backup copy job for storage policy: %s",
                self.subclient.storage_policy)
            self.dbhelper_object.run_backup_copy(self.subclient.storage_policy)

        if "synth_full" in testcase_type.lower():
            self.dbhelper_object.synthfull_backup_validation(
                self.client, self.machine_object, self.subclient)
            self.log.info("Running a incremental backup after the synthful job")
            self.log.info("Adding more data to run incremental backup")
            self.generate_test_data("automation_inc_sf", 2, 3, 50)
            self.log.info("Test Data generated before Incremental..!!")

            # run incremental backup
            self.log.info("Starting Incremental backup job")
            inc_job = self.dbhelper_object.run_backup(
                self.subclient, "Incremental", inc_with_data=True)
            # Wait for log backup to complete
            inc_job_log = self.dbhelper_object.get_snap_log_backup_job(inc_job.job_id)
            self.log.info("Log backup job with ID:%s is now completed", inc_job_log.job_id)
            if "native" in self.subclient.snapshot_engine_name.lower():
                self.log.info(
                    (
                        "Native Snap engine is being run. Backup "
                        "copy job will run inline to snap backup"))
                self.log.info("Getting the backup job ID of backup copy job")
                job = self.dbhelper_object.get_backup_copy_job(inc_job.job_id)
                self.log.info("Job ID of backup copy Job is: %s", job.job_id)

            else:
                self.log.info(
                    "Running backup copy job for storage policy: %s",
                    self.subclient.storage_policy)
                self.dbhelper_object.run_backup_copy(self.subclient.storage_policy)

        storage_policy_object = self.commcell.storage_policies.get(
            self.subclient.storage_policy)
        copy_precedence = storage_policy_object.get_copy_precedence("primary")
        self.log.info("Copy precedence of primary copy is:%s", copy_precedence)

        db_size_before = self.get_database_information()

        # stopping mysql server
        self.stop_mysql_server()
        # Restore from Primary copy
        self.run_restore(db_list=["/"], copy_precedence=copy_precedence, table_level_restore=False)

        db_size_after = self.get_database_information()

        self.validate_db_info(
            db_size_before, db_size_after)

    def snap_prerequirement_check(self, is_blocklevel=True):
        """method to check if the pre requirement to
        run snap/block level testcase is met or not

        Args:

            is_blocklevel    (bool)   -- flag to determine if the blocklevel
            testcase being run

        Raises:

            Exception:

                If client is windows

                If IntelliSnap is not enabled

                If Block level is not enabled

                If Block level testcase is being run on windows

                If sServerStartCmd regkey is not set on client

        """
        if "windows" in self.machine_object.os_info.lower():
            raise Exception("Windows doesn't support block level feature")

        self.log.info("Checking if the intelliSnap is enabled on subclient or not")
        if not self.subclient.is_intelli_snap_enabled:
            raise Exception("Intellisnap is not enabled for subclient")
        self.log.info("IntelliSnap is enabled on subclient")

        if is_blocklevel:
            self.log.info("Checking if the Block level backup is enabled on subclient or not")
            if not self.subclient.is_blocklevel_backup_enabled:
                raise Exception("Block level backup is not enabled for subclient")
            self.log.info("Block level backup is enabled on subclient")
            if "windows" in self.machine_object.os_info.lower():
                raise Exception("Block level testcases cannot be run on Windows Machine")

        self.log.info("Checking if the 'sServerStartCmd' REGKEY enabled on client or not")
        if not self.machine_object.check_registry_exists("MySQL", "sServerStartCmd"):
            raise Exception("Please set REGKEY: 'sServerStartCmd' on client")
        self.log.info("'sServerStartCmd' REGKEY enabled on client")
        self.log.info(
            "Check Basic Setting of mysql server before stating the test cases")
        self.basic_setup_on_mysql_server()
        self.log_bin_on_mysql_server()

    def blocklevel_redirect_restore(
            self, destination_client=None, destination_instance=None, is_blocklevel=True):
        """method to perform redirect restore testcase for snap and block level cases

        Args:

            destination_client    (obj)   -- Destination client object

                default: None

            destination_instance  (obj)   -- Destination Instance Object

                default: None

            is_blocklevel         (bool)  -- flag to determine if the blocklevel
            testcase being run

                default: True

        """
        if self.dbhelper_object is None:
            self.dbhelper_object = DbHelper(self.commcell)
        self.snap_prerequirement_check(is_blocklevel=is_blocklevel)
        if destination_instance:
            if not destination_client:
                destination_client = self.client
            destination_subclient = destination_instance.backupsets.get(
                'defaultdummybackupset').subclients.get('default')
        else:
            destination_instance = self.mysql_instance
            destination_client = self.client
            destination_subclient = self.subclient

        destination_mysql_helper = MYSQLHelper(
            self.commcell,
            destination_subclient,
            destination_instance,
            destination_client.client_hostname,
            destination_instance.mysql_username)

        # populate test data
        self.generate_test_data()
        self.log.info("Test Data generated..!!")

        ###################### Running Full Backup ########################
        self.log.info("Starting FULL backup job")
        full_job = self.dbhelper_object.run_backup(self.subclient, "FULL")

        full_job_log = self.dbhelper_object.get_snap_log_backup_job(full_job.job_id)
        self.log.info("Log backup job with ID:%s is now completed", full_job_log.job_id)

        if "native" in self.subclient.snapshot_engine_name.lower():
            self.log.info(
                (
                    "Native Snap engine is being run. Backup "
                    "copy job will run inline to snap backup"))
            self.log.info("Getting the backup job ID of backup copy job")
            job = self.dbhelper_object.get_backup_copy_job(full_job.job_id)
            self.log.info("Job ID of backup copy Job is: %s", job.job_id)

        else:
            self.log.info("Snap engine is not native.")
            ###### Run backup copy job #########
            self.log.info(
                "Running backup copy job for storage policy: %s",
                self.subclient.storage_policy)
            copy_precedence = self.dbhelper_object.run_backup_copy(
                self.subclient.storage_policy)
            self.log.info(
                "Copy precedence of 'primary snap' copy is: %s",
                copy_precedence)

        #### Redirect Restore to same instance
        storage_policy_object = self.commcell.storage_policies.get(
            self.subclient.storage_policy)
        copy_precedence = storage_policy_object.get_copy_precedence("primary")
        self.log.info("Copy precedence of primary copy is: %s", copy_precedence)

        db_size_before = self.get_database_information()

        source_data_dir = self.data_directory
        data_directory = destination_mysql_helper.data_directory
        redirect_to = "{0}_red".format(data_directory)
        redirect_path = "{0}\u0015{1}".format(source_data_dir, redirect_to)

        config_file_location = destination_instance.config_file
        config_file_destination = "{0}.orig".format(config_file_location)
        destination_mysql_helper._redirect_operations(
            config_source=config_file_location, config_destination=config_file_destination)

        destination_mysql_helper.stop_mysql_server()
        # Restore from Primary copy
        self.run_restore(
            db_list=["/"],
            copy_precedence=copy_precedence,
            redirect_path=redirect_path,
            destination_client_name=destination_client.client_name,
            destination_instance_name=destination_instance.instance_name)

        db_size_after = destination_mysql_helper.get_database_information()

        self.validate_db_info(
            db_size_before, db_size_after)

        destination_mysql_helper._redirect_operations(redirect_directory=redirect_to)

        self.log.info("Restoring the config file")
        destination_mysql_helper._redirect_operations(
            config_source=config_file_destination, config_destination=config_file_location)
        self.log.info("Trying to start the server")
        destination_mysql_helper.start_mysql_server()

    def _redirect_operations(
            self,
            redirect_directory=None,
            config_source=None,
            config_destination=None):
        """method to perform operations related to redirect restore

        Args:

            redirect_directory  (str)   --  postgres redirect directory path

                default: None

            config_source       (str)   --  config file source path

                default: None

            config_destination  (str)   --  config file destination path

                default: None

        """
        if redirect_directory:
            self.log.info("Stopping restored server")
            self.stop_mysql_server()
            self.log.info("Cleaning up redirected path")
            self.machine_object.remove_directory(redirect_directory)
            self.log.info("Redirected directory is removed")
        if config_source and config_destination:
            if self.machine_object.check_file_exists(config_destination):
                self.machine_object.remove_directory(config_destination)
            self.log.info(
                "Copying config file:%s to:%s",
                config_source, config_destination)
            self.machine_object.copy_file_locally(
                config_source, config_destination)

    def innodb_file_per_table(self):
        """ Checks if the innodb_file_per_table is enabled
        in the server or not

        Returns:

            (bool) -- Returns True if the flag is enabled
                      Returns false if the flag is disabled

        Raises:
            Exception:
                if unable to get innodb_file_per_table value
        """
        try:
            self.db_connect = database_helper.MySQL(
                self.host_name, self.usr, self.pwd, self.port)
            query = "show variables like 'innodb_file_per_table';"
            response_object = self.db_connect.execute(query)
            return response_object.rows[0][1].lower() == "on"

        except Exception:
            raise Exception(
                "Unable to get innodb_file_per_table value")

    def is_xtrabackup_eligible(self):
        """checks if the server is eligible to run xtrabackup

        Returns:
            (bool)  --  Returns True if eligible
                        Returns False if not eligible

        """
        if self.mysql_instance is None:
            self.mysql_instance = self.machine_object.client_object.\
                agents.get("MySQL").\
                instances.get(self._mysql_instance_name)
        if "windows" in self.machine_object.os_info.lower():
            self.log.info("Windows doesn't support xtrabackup")
            return False
        if not self.mysql_instance.is_xtrabackup_enabled:
            self.log.info("xtrabackup is not enabled in the instance property")
            return False
        if not self.innodb_file_per_table():
            self.log.info("innodb_file_per_table is not ON")
            return False
        version = self.mysql_instance.version
        if int(re.split(r"\D", version)[0]) >= 5:
            if int(re.split(r"\D", version)[0]) == 5 and int(re.split(r"\D", version)[1]) < 6:
                return False
            return True
        return False

    def is_xtrabackup_effective(self, backup_job, client_log_directory=None):
        """method to check if the xtrabackup is being used for the backup

        Args:
            backup_job  (str)           --  Backup job ID
            client_log_directory(str)   --  Client log directory
                default: None

        Returns:
            (bool)  --  True if xtrabackup is effective
                        False if xtrabackup is not effective

        Raises:
            Exception:
                If client machine is windows

                If failed to run command in the client

        """
        if self.client:
            mysql_log = self.machine_object.join_path(
                self.client.log_directory, "MySqlBackupChild.log")
        else:
            if client_log_directory:
                mysql_log = self.machine_object.join_path(
                    client_log_directory, "MySqlBackupChild.log")
            else:
                raise Exception("Set client object or provide client log directory")
        if "windows" in self.machine_object.os_info.lower():
            raise Exception("Windows doesn't support xtrabackup")
        output = self.machine_object.execute_command(
            "cat %s | grep %s| awk '{for(i=1;i<=NF;i++)if($i~/xtraBackupFlag/)print $(i+1)}' | head -n 1" %(
                mysql_log, backup_job))
        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)
        return "[1]" in output.formatted_output

    def backup_job_ran_on(self, backup_job):
        """method to get the client and instance details on which backup job was run

        Args:
            backup_job   (obj)   --  Backup job object

        Returns:
            (list)  --  List containing [client_name, instance_name, job_status]

        Raises:

            Exception:

                If could not get the backup job run details

        """

        try:
            query = "select dbo.getMysqlProxyAndInstance({0},{1})".format(
                backup_job.job_id, self.subclient.subclient_id)
            self.csdb.execute(query)
            details = self.csdb.fetch_one_row()[0].split("\\")
            details.extend([backup_job.status])
            return details
        except Exception:
            raise Exception("Could not get the backup job run details ")

    def populate_database(self, subclient_content=None, comment_string=""):
        """Inserts test tables and views in the each
        database in the subclient content

        Args:
            subclient_content (list)    --  databases in the subclient

                    default: None

            comment_string      (str)   --  Comment string to be checked in create table
            command

                    default: ""

        """
        # Timestamp For Tablenames
        timestamp_full = str(int(time.time()))
        self.log.info("Populating Databases before Backup")
        if not subclient_content and not self.subclient:
            raise Exception("Subclient content needs to passed to the method")
        if not subclient_content:
            subclient_content = self.subclient.content
        for each_db in subclient_content:
            table_list = self.create_table_with_text_db(
                each_db,
                table_name="full_{0}".format(timestamp_full),
                no_of_tables=10,
                column_in_each_table=5,
                drop_table_before_create=False,
                comment_string=comment_string)
            each_db = each_db.strip("/")
            each_db = each_db.strip("\\")
            for table in table_list:
                self.create_view(
                    "select count(*) from `{0}`".format(table),
                    "TestView_{0}".format(table),
                    database_name=each_db)

    def run_proxy_backup(
            self,
            backup_type,
            inc_with_data=False,
            testcase_type="PROXY_ACC1",
            truncate_logs_on_source=False,
            do_not_truncate_logs=False):
        """Initiates the backup job on proxy subclient and checks if the proxy is honored

            Args:

                backup_type    (str)   -- Backup type to perform on subclient
                Either FULL or INCREMENTAL

                inc_with_data  (bool)  --  flag to determine if the incremental backup
                includes data or not

                testcase_type  (str)   --  Testcase type which is being run

                    default:         "PROXY ACC1"

                    Accepted Values: PROXY_ACC1/PROXY_FAILOVER/DO_NOT_TRUNCATE_LOGS_ON_PROXY

                truncate_logs_on_source (bool)  --  flag to determine if the logs to be
                truncated on master client

                    default: False

                do_not_truncate_logs    (bool)  --  flag to determine if the proxy logs
                needs to be truncated or not

                    default: False

            Returns:
                job            (obj)   -- Returns Job object

            Raises:
                Exception:

                    if proxy settings are not honored

                    if unable to run backup job

        """
        self.log.info("#####Starting Subclient %s Backup#####", backup_type)
        if inc_with_data or truncate_logs_on_source or do_not_truncate_logs:
            job = self.subclient.backup(
                backup_type, inc_with_data=inc_with_data,
                truncate_logs_on_source=truncate_logs_on_source,
                do_not_truncate_logs=do_not_truncate_logs)
        else:
            job = self.subclient.backup(backup_type)
        self.log.info(
            "Started %s backup with Job ID: %s", backup_type, job.job_id)

        if "FULL" in backup_type:
            self.log.info("Checking if the proxy backup is effective")
            details = self.backup_job_ran_on(job)
            if "completed" not in details[2].lower():
                while job.phase.lower() not in ['scan', 'backup'] \
                    and "pending" not in job.status.lower() and \
                    "completed" not in job.status.lower():
                    time.sleep(2)
                if "proxy_failover" in testcase_type.lower() and \
                        self.subclient.is_failover_to_production:
                    if not (details[0] == self.client.client_name and \
                            details[1] == self.mysql_instance.instance_name):
                        raise Exception(
                            "In PROXY_FAIL_OVER testcase, backup job is expected to run on Master")
                else:
                    if not (self.mysql_instance.proxy_options['clientName'] == details[0] and \
                                self.mysql_instance.proxy_options['instanceName'] == details[1]):
                        raise Exception("Backup job is expected to run on proxy client")
            self.log.info("Proxy is honored during backup job")

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )
        self.log.info("Successfully finished %s backup job", backup_type)

        if self.mysql_instance.proxy_options.get('runBackupOnProxy', False):
            details = self.backup_job_ran_on(job)
            if not (details[0] == self.client.client_name and \
                details[1] == self.mysql_instance.instance_name):
                raise Exception(
                    "Transactional logs are expected to run on Master. Please check the logs")
        return job

    def proxy_testcase(self, testcase_type="PROXY_ACC1"):
        """method to run proxy testcases

        Args:
            testcase_type  (str)   --  Testcase type which is being run

                    default:         "PROXY ACC1"

                    Accepted Values: PROXY_ACC1/PROXY_FAILOVER/DO_NOT_TRUNCATE_LOGS_ON_PROXY

        """
        self.log.info("Proxy testcase being run is:%s", testcase_type)
        self.log.info(
            "Check Basic Setting of mysql server before stating the test cases")
        proxy_client = self.commcell.clients.get(self.mysql_instance.proxy_options['clientName'])
        agent_object = proxy_client.agents.get('MySQL')
        proxy_instance = agent_object.instances.get(
            self.mysql_instance.proxy_options['instanceName'])
        proxy_backupset = proxy_instance.backupsets.get('defaultdummybackupset')
        proxy_subclient = proxy_backupset.subclients.get('default')
        proxy_helper_object = MYSQLHelper(
            self.commcell,
            proxy_subclient,
            proxy_instance,
            proxy_client.client_hostname,
            proxy_instance.mysql_username)
        proxy_database_object = database_helper.MySQL(
            proxy_client.client_hostname,
            proxy_helper_object.usr, proxy_helper_object.pwd, proxy_helper_object.port)
        proxy_database_object.start_slave()
        self.subclient.is_failover_to_production = False

        self.basic_setup_on_mysql_server()

        ### Checking whether Binary Logging is enabled or not in MySQL Server
        self.log_bin_on_mysql_server()

        #### check if the proxy is enabled on instance and subclient

        if not(self.mysql_instance.proxy_options[
                'isProxyEnabled'] and self.subclient.is_proxy_enabled):
            raise Exception("Check if the proxy is enabled on instance and subclient")

        self.log.info("Read subclient content")
        self.log.info("Subclient Content: %s", self.subclient.content)

        if self.subclient.content == [] or self.subclient.content == ['/']:
            raise Exception(
                "Subclient Content is empty please add subclient content from Commcell Console"
            )
        contents = self.subclient.content.copy()
        contents = [database.strip("/") for database in contents]
        contents = [database.strip("\\") for database in contents]

        if 'mysql' in contents:
            contents.remove('mysql')
        if 'sys' in contents:
            contents.remove('sys')

        ### Populating Databases For Full Backup
        self.populate_database()

        if "proxy_failover" in testcase_type.lower():
            if not self.subclient.is_failover_to_production:
                self.subclient.is_failover_to_production = True
            proxy_database_object.stop_slave()

        if "do_not_truncate_logs_on_proxy" in testcase_type.lower():
            binary_log_info_before = proxy_database_object.get_binary_logs()
            self.run_proxy_backup(
                'FULL', False, testcase_type, do_not_truncate_logs=True)

        else:
            ### Running Full Backup
            self.run_proxy_backup('FULL', False, testcase_type)

            ### Running Incremental Backup
            self.run_proxy_backup('INCREMENTAL', False, testcase_type)

            ### Getting Database Size and table sizes (Incremental 2)
            database_info = self.get_database_information(
                contents)

            ### drop all subclient contents
            self.cleanup_database_contents(contents)
            self.log.info("Dropped all database contents before restore")
            ### Running In Place Data + Log Restore
            self.log.info("Running In Place Restore - Data + Log")
            self.run_restore(["/"])

            ### Getting Database Size and table sizes (Incremental 2)
            data_after_restore = self.get_database_information(
                contents)

            self.log.info("###Starting data validation after restore###")
            # validating data after restore
            self.validate_db_info(
                database_info,
                data_after_restore)

            if "proxy_failover" in testcase_type.lower():
                if self.subclient.is_failover_to_production:
                    self.subclient.is_failover_to_production = False
                proxy_database_object.reconnect()
                proxy_database_object.start_slave()

        if "do_not_truncate_logs_on_proxy" in testcase_type.lower():
            binary_log_info_after = proxy_database_object.get_binary_logs()
            if binary_log_info_after[1] < binary_log_info_before[1] and \
                binary_log_info_after[2] < binary_log_info_before[2]:
                raise Exception(
                    "Do not truncate logs on proxy was selected during backup, "
                    "logs on proxy before backup was expected to be more or "
                    "equal to number of logs after backup")

            self.log.info("Logs in proxy were not truncated")

    def _get_mysql_database_connection(self, database=None):
        """
        Get the mysql database connection
        Args:
                database    (str)  -- Database name
                            default value None
            Returns:
                Mysql database connection object
        """

        if str(self.port).find(":") >= 0:

            mysql_db_connection_object = database_helper.MySQL(self.host_name,
                                                               self.usr, self.pwd, self.mysql_port, database,
                                                               self.ssl_ca, self.ssl_key, self.ssl_cert)

            self.mysql_db_connection_object = mysql_db_connection_object
        else:

            mysql_db_connection_object = database_helper.MySQL(
                self.host_name, self.usr, self.pwd, self.port, database)

            self.mysql_db_connection_object = mysql_db_connection_object

        return self.mysql_db_connection_object

    def run_data_restore_and_validation(self, dest_client_name=None, dest_instance_name=None,
                                        data_restore=True, log_restore=False, from_time=None,
                                        to_time=None, browse_jobid=None, database_info=None,
                                        meb_restore=False, temporary_staging=None):
        """method to run inplace restore and validate data after restore

            Args:
                dest_client_name    (str)   --  destination Client name

                default: None

                dest_instance_name  (str)   --  destination MySQL Instance name

                default: None

                data_restore   (bool)  -- data restore flag

                default: True

                log_restore    (bool)  -- log restore flag

                default: True

                from_time   (int)  -- from time value of job

                default: None

                to_time    (int)  -- to time value of job

                default: None

                browse_jobid    (int)  -- browse job id for restore

                default: None

                database_info  (dict)  -- database information to validate \
                    against the data after restore

                default: None

                meb_restore		(bool)  -- flag if the restore is meb or not

                default: False

                temporary_staging   (str)  -- staging location to be used in restore

                default: None

            Raises:
                Exception:

                    if database information dict is not provided

                    if failed to run restore job

        """
        try:
            # Removing mysql and sys system db's from restore list for traditional restore.
            # If MEB restore, restoring all the databases ["/"].
            if meb_restore:
                paths = ["/"]
                log_restore = True
            else:
                if database_info is None:
                    raise Exception("database information needed to validate the data after "
                                    "restore")
                paths = self.subclient.content.copy()
                if '\\mysql' in paths:
                    paths.remove('\\mysql')
                if '\\sys' in paths:
                    paths.remove('\\sys')
            self.log.debug(paths)

            # Assign the value of staging directory based on functionality
            if meb_restore:
                if temporary_staging is not None:
                    staging = temporary_staging
                else:
                    staging = self.mysql_instance.log_data_directory
            elif self.is_cloud_db:
                staging = self.mysql_instance.instance_name
            else:
                staging = self.client.job_results_directory

            # Submitting restore job request
            if meb_restore:
                job = self.subclient.restore_in_place(paths, staging,
                                                      dest_client_name=dest_client_name,
                                                      dest_instance_name=dest_instance_name,
                                                      data_restore=data_restore,
                                                      log_restore=log_restore,
                                                      from_time=from_time,
                                                      to_time=to_time,
                                                      browse_jobid=browse_jobid)
            else:
                job = self.mysql_instance.restore_in_place(paths,
                                                           staging,
                                                           data_restore=data_restore,
                                                           log_restore=log_restore)

            self.log.info("Started restore with Job ID: %s", job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore job with error: {1}".format(
                        job.delay_reason))
            self.log.info("Successfully finished restore job")

            if meb_restore:
                return job
            else:
                # Setting sleep time for streaming restore
                if (data_restore and log_restore) or log_restore:
                    self.log.info("Sleep for 5 minutes after log restore")
                    time.sleep(300)
                else:
                    self.log.info("Sleep for a minute after data restore")
                    time.sleep(60)

                data_after_restore = self.get_database_information(self.subclient.content)
                self.log.info("###Starting data validation after restore###")

                # validating data after restore
                self.validate_db_info(database_info, data_after_restore)
            return job

        except Exception as excp:
            self.log.exception("An error occurred while running restore and validation")
            raise excp

    def delete_table_for_dependent_views(self, database_list):
        """ Deletes first two tables having dependent views from all
            the databases provided in database list

                Args:
                    database_list     (list)  -- list of databases

                Raises:
                    Exception:
                        if database list is empty
        """
        try:
            tables_to_be_deleted = []
            if database_list is None:
                raise Exception("Database list to delete dependent view is empty")

            for database in database_list:
                table_list = self.get_tables_list_for_db(database)
                for table in table_list[:2]:
                    self.drop_table(database, table)
                    tables_to_be_deleted.append(table)
            return tables_to_be_deleted
            self.log.info("First two tables having dependent views are dropped from databases")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)

    def get_job_event_description_with_severity_six(self, job_events):
        """ Gets the events description from job having severity as 6

            Args:
                job_events          (dict)  -- Job events

            Raises:
                Exception:
                    if unable to get job events with severity 6
        """
        try:
            database_list = list()
            major_event_description = list()
            for i in job_events:
                if i['severity'] == 6 and i['description'].startswith('Backup of [~'):
                    severe_event_details_list = list(i['description'].split("~"))
                    database_list.append(severe_event_details_list[1])
                    major_event_description.append(severe_event_details_list[3])
            return database_list, major_event_description

        except Exception:
            self.log.error("Exception in getting major event description from job")
            raise Exception("Unable to get job events description with severity 6")

    def get_sbt_image_for_meb_operation(self, job_id, operation='backup'):
        """ Method to get sbt image name for meb operation from client machine logs

        Args:
            job_id  (str)       --  Backup or restore job ID

            operation(str)      --  Backup phase to check for

                Accepted values: backup/restore

                default: backup

        Returns:
            True if the backup phase specified is run on standby node
            False otherwise

        """
        try:
            # Fetching client machine log directory
            log_path = self.client.log_directory

            # Getting log file name to search the sbt image
            if 'backup' in operation.lower():
                log_path = self.machine_object.join_path(log_path, 'MySqlBackupParent.log')
            else:
                log_path = self.machine_object.join_path(log_path, 'CvMySqlSBTRestore.log')

            command = f"cat {log_path} | grep {job_id} | grep \'runCommand\'"
            output = self.machine_object.execute_command(command)

            if output.exception_message != '':
                raise Exception("Unable to fetch sbt image name for MEB operation from client "
                                "machine logs")

            sbt_image_list = re.findall(r'sbt:[0-9_]*', output.output)

            # Raising exception is sbt image list is empty
            if not sbt_image_list:
                raise Exception("sbt image name list is empty")

            return sbt_image_list

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)

    def check_comments_in_table(self, database_list=None, comment_string=""):
        """ method to verify comment string in create table command

        Args:
            database_list       (list)   --  Database name

                default: None

            comment_string      (str)   --  Comment string to be checked in create table
            command

                default: ""

        Returns:
            True if the comment count matches correctly in create table statement of all the
            tables
            False otherwise

        Raises:
            Exception:
                Mismatch in count of comments

        """
        try:
            table_list_info_database = {}
            for database in database_list:
                tb_list = self.get_tables_list_for_db(database)
                # Creating a dictionary for storing list of tables of each databases
                table_list_info_database[database] = tb_list
            for db_name in table_list_info_database:
                for tables in table_list_info_database[db_name]:
                    query = "show create table `%s`.`%s`;" % (db_name, tables)
                    self.mysql_db_connection_object = self._get_mysql_database_connection(
                        database=db_name)
                    response = self.mysql_db_connection_object.execute(query)
                    create_table_statement_string = list(response.rows)[0][1]
                    comment_count = create_table_statement_string.count(comment_string)
                    if comment_count != 2:
                        message = "Comment count mismatch in table `%s`.`%s`;" % (db_name, tables)
                        self.log.info(message)
                        raise Exception("Comment count mismatch in create table statement")
                    else:
                        return True
            return False

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)

    def verify_no_lock_parameter_in_meb_command(self, job_id):
        """ Method to verify no lock parameters in meb backup command from client machine logs

        Args:
            job_id      (str)   --  Backup job ID of MySQL Enterprise backup

        Returns:
            True if the No Lock parameters are found in MEB backup command

        Raises:
            Exception:
                No Lock parameters no found in backup command for backup job id

        """
        # Fetching client machine log directory
        log_path = self.client.log_directory

        # Getting log file name to search the mysqlbackup command
        log_path = self.machine_object.join_path(log_path, 'MySqlBackupParent.log')

        command = f"cat {log_path} | grep {job_id} | grep \'runCommand\'"
        output = self.machine_object.execute_command(command)

        if output.exception_message != '':
            raise Exception("Unable to verify no lock parameters for MEB backup operation from "
                            "client machine logs")

        # Check no lock parameter string in MEB backup job
        if "--no-locking --skip-binlog" not in output.output:
            raise Exception("No Lock parameters not found in MEB backup command in job_id `%s`"
                            % job_id)
        else:
            self.log.info("Verified no lock parameter in MEB backup job: %s", job_id)
            return True

    def verify_meb_properties_on_instance(self, source_instance, destination_instance=None,
                                          source_meb_bin_path=None):
        """ Method to verify if MEB is enabled, set the MEB bin path on source MySQL Instance

        Args:
            source_instance         (obj)   --  Object of MySql Source Instance

            destination_instance    (obj)   --  Object of MySql Destination Instance

            source_meb_bin_path     (str)   --  MEB binary path of Source Instance to be set in
            MySQL Instance Property for backup and restore operations

        Returns:
            MEB details of source MySQL Instance if enabled or not

        Raises:
            Exception:
                If MySQL Enterprise Backup is not enabled on destination MySQL Instance

        """

        if source_instance is None:
            source_instance = self.mysql_instance

        if destination_instance:
            if destination_instance.name != source_instance.name:
                # Checking value if MEB enabled in Destination MySQL Instance before execution
                if not destination_instance.mysql_enterprise_backup_binary_path['enableMEB']:
                    raise Exception("MySQL Enterprise backup not enabled in destination MySQL "
                                    "Instance")

        # Check MySQL Enterprise Backup in Source MySQL Instance Property
        meb_info = source_instance.mysql_enterprise_backup_binary_path
        self.log.info("MEB Binary path property before execution of test case %s",
                      meb_info)

        # Checking the value of MEB enabled before starting execution of test case
        if meb_info['enableMEB']:
            meb_existing_flag_on_source_instance = True
        else:
            meb_existing_flag_on_source_instance = False

        # Setting the value of MEB bin path if MEB is not enabled or if different value of
        # binary path is set in MySQL Instance Property
        if (not meb_info['enableMEB'] or (meb_info['mebBinPath'] !=
                                          source_meb_bin_path)):
            source_instance.mysql_enterprise_backup_binary_path = source_meb_bin_path
        return meb_existing_flag_on_source_instance

    def run_meb_backup_flow(self, check_no_lock_flag=False):
        """ Method to run the backup flow i.e one full backup followed by two incremental backups
        for MySQL Enterprise Backup functionality.

        Args:

            check_no_lock_flag      (bool)  --   Checks no lock status in backup commands

        Returns:
            1. The list of automation created databases for full and increment backup
            2. Size of databases collected after second Incremental backup (for data validation)
            3. Job object of second Incremental backup
            4. List of MySQL Enterprise backup SBT images of full and incremental backup
        """
        try:
            if self.dbhelper_object is None:
                self.dbhelper_object = DbHelper(self.commcell)

            self.log.info("No lock status to be checked in MEB backup flow %s ",
                          check_no_lock_flag)

            # Populating Databases For Full Backup
            self.generate_test_data(database_prefix="automation_cv_full")

            # Running Full Backup
            full_backup = self.dbhelper_object.run_backup(self.subclient, 'FULL')

            sbt_image_full_backup = self.get_sbt_image_for_meb_operation(
                full_backup.job_id)

            # Check no lock parameters in MEB backup job command if flag is set
            if check_no_lock_flag:
                self.verify_no_lock_parameter_in_meb_command(full_backup.job_id)

            # Refreshing sub-client content to get updated database list after full backup
            self.subclient.refresh()
            db_list_full_backup = self.subclient.content

            # Populating Databases For first incremental backup
            db_list_inc1_backup = self.generate_test_data(
                database_prefix="automation_cv_inc1")

            # Running Second Incremental Backup for MySql Enterprise Backup
            inc_backup_1 = self.dbhelper_object.run_backup(self.subclient, 'INCREMENTAL')

            sbt_image_inc_backup_1 = self.get_sbt_image_for_meb_operation(
                inc_backup_1.job_id)

            # Check no lock parameters in MEB backup job command if flag is set
            if check_no_lock_flag:
                self.verify_no_lock_parameter_in_meb_command(inc_backup_1.job_id)

            # Populating Databases For second incremental backup
            db_list_inc2_backup = self.generate_test_data(
                database_prefix="automation_cv_inc2")

            # Running Second Incremental Backup for MySql Enterprise Backup
            inc_backup_2 = self.dbhelper_object.run_backup(self.subclient, 'INCREMENTAL')

            sbt_image_inc_backup_2 = self.get_sbt_image_for_meb_operation(
                inc_backup_2.job_id)

            # Check no lock parameters in MEB backup job command if flag is set
            if check_no_lock_flag:
                self.verify_no_lock_parameter_in_meb_command(inc_backup_2.job_id)

            # Getting Database Size and table sizes (Incremental 2)
            db_size_after_inc2_bkp = self.get_database_information()

            self.log.info("MEB Backup sbt images -> %s ", (sbt_image_full_backup +
                                                           sbt_image_inc_backup_1 +
                                                           sbt_image_inc_backup_2))
            return db_list_full_backup + db_list_inc1_backup + db_list_inc2_backup, \
                   db_size_after_inc2_bkp, inc_backup_2, sbt_image_full_backup + \
                   sbt_image_inc_backup_1 + sbt_image_inc_backup_2

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            raise Exception("Exception in meb backup flow")

    def run_meb_restore_flow(self, dest_client_name=None, dest_instance_name=None,
                             from_time=None, to_time=None, browse_jobid=None,
                             temporary_staging=None):
        """ Method to run browse and restore from second incremental MEB backup

        Args:
            dest_client_name        (str)   --  Destination MySQL client name

            dest_instance_name      (str)   --  Destination MySQL instance name

            from_time               (int)   --  from time value of backup job used for browse

            to_time                 (int)   --  end time value of backup job used for browse

            browse_jobid            (int)   --  backup job id to be used for browse operation

            temporary_staging       (str)   -- temporary stating location for MEB Restore (For MEB
            Restore, it is the Log directory of destination MySQL Instance)

        Returns:
            Restore job object
        """
        try:
            restore_job = self.run_data_restore_and_validation(
                dest_client_name=dest_client_name,
                dest_instance_name=dest_instance_name, from_time=from_time,
                to_time=to_time, browse_jobid=browse_jobid, meb_restore=True,
                temporary_staging=temporary_staging)
            return restore_job

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            raise Exception("Exception in meb restore flow")

    def validate_meb_data_and_image(self, database_info, db_list_for_restore_validation,
                                    restore_job_id, meb_backup_sbt_image):
        """Method to validate meb data and sbt image after MEB restore operation

        Args:

            database_info                   (dict)  --  database info of source MySQL Server to
            be validated

            db_list_for_restore_validation  (list)  --  database list to get database info of
            destination MySQL Server

            restore_job_id                  (str)   --  MySql Enterprise Backup Restore job ID

            meb_backup_sbt_image            (list)  --  List of sbt images of backups

        """
        data_after_restore = self.get_database_information(db_list_for_restore_validation)
        self.log.info("###Starting data validation after restore###")

        # validating data after restore
        self.validate_db_info(database_info, data_after_restore)

        # Get list of sbt images from the restore meb job
        meb_restore_sbt_image = self.get_sbt_image_for_meb_operation(restore_job_id,
                                                                     operation='restore')
        self.log.info("MEB Restore sbt images -> %s ", meb_restore_sbt_image)
        if meb_backup_sbt_image == meb_restore_sbt_image:
            self.log.info("Validated sbt images for backup and restore")
        else:
            raise Exception("sbt image validation failed")

    def fetch_mysql_variant_name_from_version(self):
        """ Method to get the mysql variant name from the mysqld version command

        Returns:
            MySQL Server Variant Name
        """
        try:
            if self.machine_object.os_info.lower() == "windows":
                mysqld_bin_path = self.mysql_instance.binary_directory
                # In Powershell, to run the command that contains a space, command needs to be
                # preceeded with ampersand &
                get_mysqld_version_command = '&"' + mysqld_bin_path + 'mysqld" --version'
                version_output = self.machine_object.execute_command(get_mysqld_version_command)

            else:
                # Path of mysqld binary may differ from the one in MySQL Instance binary
                # directory in case of Unix/Linux
                get_mysqld_bin_path_command = "which mysqld"
                bin_path_output = self.machine_object.execute_command(get_mysqld_bin_path_command)
                if bin_path_output.exception_message:
                    raise Exception(bin_path_output.exception_message)
                elif bin_path_output.exception:
                    raise Exception(bin_path_output.exception)
                else:
                    mysqld_bin_path = bin_path_output.formatted_output

                get_mysqld_version_command = mysqld_bin_path + " --version"
                version_output = self.machine_object.execute_command(get_mysqld_version_command)

            if version_output.exception_message:
                raise Exception(version_output.exception_message)
            elif version_output.exception:
                raise Exception(version_output.exception)
            else:
                version_string = version_output.formatted_output

            if "Percona" in version_string:
                mysql_variant_name = "Percona"
            elif "MariaDB" in version_string:
                mysql_variant_name = "MariaDB"
            else:
                mysql_variant_name = "MySQL"
            return mysql_variant_name

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            raise Exception("Exception in getting mysql server variant name")

    def acceptance_test_case_traditional(self, mysql_variant_name=None):
        """Method to execute acceptance test case for MySQL iDA traditional for various mysql
        variants

        Args:

            mysql_variant_name              (str)  --  name of mysql variant

                default: None

                Accepted Values: MySQL/ MariaDB/ Percona

        """
        # Check if client is windows and mysql variant is Percona Server
        if self.machine_object.os_info.lower() == "windows" and mysql_variant_name == "Percona":
            raise Exception("Percona Server is currently not supported on Windows, "
                            "please provide a Unix/Linux client")

        if mysql_variant_name is None:
            mysql_variant_name = self.fetch_mysql_variant_name_from_version()
            self.log.info("The MySQL Variant from server version is %s ", mysql_variant_name)
        else:
            # Compare the mysql variant name input value and the one fetched from version command
            if mysql_variant_name not in ("MySQL", "MariaDB", "Percona"):
                raise Exception("Not an accepted value for mysql variant name")
            elif mysql_variant_name == self.fetch_mysql_variant_name_from_version():
                self.log.info("MySQL Variant name matched")
            else:
                raise Exception("Mismatch in MySQL Variant name, kindly check value passed "
                                "in argument and server information")

        if self.dbhelper_object is None:
            self.dbhelper_object = DbHelper(self.commcell)

        # Checking the basic settings required for Automation
        self.log.info(
            "Check Basic Setting of mysql server before stating the test cases")
        self.basic_setup_on_mysql_server()
        self.log_bin_on_mysql_server()

        if not self.subclient.is_default_subclient:
            raise Exception("Please provide default subclient name as input")

        # Populating Databases For Full Backup
        self.generate_test_data(database_prefix="automation_full")

        # Running Full Backup
        self.dbhelper_object.run_backup(self.subclient, 'FULL')

        # Populating Databases For INC 1 Backup
        db_list = self.generate_test_data(database_prefix="automation_inc1")

        # Running Incremental data + log Backup
        self.dbhelper_object.run_backup(self.subclient, 'INCREMENTAL')

        # Getting Database Size and table sizes (Full/1st incr)
        db_size_full_bk = self.get_database_information()

        self.get_default_subclient_contents()

        # Getting Database Size and table sizes (Incremental 2)
        self.populate_database(db_list)

        # Running Incremental Backup
        self.dbhelper_object.run_backup(self.subclient, 'INCREMENTAL')

        # Getting Database Size and table sizes (2nd incr)
        db_size_inc2_bk = self.get_database_information()

        self.cleanup_test_data(database_prefix='automation')

        # Running In Place Data Only Restore
        self.log.info("Running In Place Restore - Data Only")
        self.run_data_restore_and_validation(database_info=db_size_full_bk)

        # Running In Place Log Only Restore
        self.log.info("Running In Place Restore - Log Only")
        self.run_data_restore_and_validation(
            data_restore=False, log_restore=True, database_info=db_size_inc2_bk)

        self.cleanup_test_data(database_prefix='automation')

        # Running In Place Data + Log Restore
        self.log.info("Running In Place Restore - Data + Log")
        self.run_data_restore_and_validation(
            log_restore=True, database_info=db_size_inc2_bk)

    def check_table_engine(self, database_name, engine):
        """
        Validate table engine in a database is same as expected
        Args:
            database_name (str) : name of database to be checked
            engine        (str) : expected engine name (MyISAM, InnoDB)
        """
        self.log.info(f"Checking tables in {database_name} for engine type {engine}")
        self.mysql_db_connection_object = self._get_mysql_database_connection(database=database_name)
        tables = self.get_tables_list_for_db(database_name)
        for table_name in tables:
            query = f"show table status like '{table_name}';"
            response = self.mysql_db_connection_object.execute(query)
            table_engine = response.rows[0][1]
            if table_engine != engine:
                self.log.error(f"expected engine type {engine} not same as table engine {table_engine}")
                raise Exception('table Engine not same as expected value')
            self.log.info(f"expected engine type {engine} same as table engine {table_engine}")
