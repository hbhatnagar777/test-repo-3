# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing Hive operations.

This file consists of a class named: HiveHelper, which can connect to the connects to the cluster
performs Hive specific operations.

The instance of this class can be used to perform various operations on a Hadoop Cluster, like,

    #.  Generating test data on hive
    #.  Modifying test data on hive
    #.  Validating table data between two hive databases

HiveHelper
=============

    __init__()                          --  Initialize instance of the hive helper class

    __init_kinit()                      --  Runs kinit for hdfs & hive principal using keytab file

    __run_command()                     --  Runs a command on hive node

    __parse_query_output()              --  Parses the beeline query output by removing unnecessary symbols/details

    __run_query()                       --  Executes the query using beeline and returns the output

    __list_databases()                  --  List all the databases based on prefix

    create_database()                   --  Creates a database with given name

    drop_database()                     --  Drops the database with given name

    _fetch_database_data()              --  Fetches the table data for a given database/specified tables

    __list_tables()                     --  List all the tables in given database

    __create_table()                    --  Constructs a create query based on given arguments and executes it

    __drop_table()                      --  Drops table if exists

    __select_count()                    --  Returns no of rows by running select command on table

    __get_row_count()                   --  Returns no of rows by running select/show tblproperties command on table

    __describe_formatted_table()        --  Returns output of describe formatted command on table

    __select_all_from_table()           --  Returns output of select all command on table

    __fetch_table_data()                --  Returns output of select all command on table

    __insert_into_table()               --  Inserts data into given table

    __update_table()                    --  Updates row data in the table based on given row_id and value

    __delete_from_table()               --  Deletes given row from the table

    __acid_the_table()                  --  Runs acid operations on given table

    __compact_the_table()               --  Runs compact operation on the given table

    __is_table_exists()                 --  Checks if table exists

    __is_table_empty()                  --  Checks if table is empty

    __is_table_transactional()          --  Checks if table is transactional/acid supported

    __is_table_partitioned()            --  Checks if table is partitioned

    __analyze_table()                   --  Runs analyze command on table

    __repair_table()                    --  Runs repair command on table

    __create_directory()                --  Creates a directory in hdfs and runs chown command with given owner

    generate_test_data()                --  Creates tables in specified database and generates data into table

    validate_test_data()                --  Validates source and destination table data

    acid_the_tables()                   --  Runs acid operations on given list of table identifiers

    insert_into_tables()                --  Inserts data into list of table_identifiers or given database

    get_tables()                        --  Returns list of table_identifiers from given list of databases

    drop_tables()                       --  Drops list of table_identifiers or given database based on contains value

"""
import copy
import time
import itertools
import pandas as pd

from faker import Faker
from datetime import datetime

from AutomationUtils import logger
from AutomationUtils.machine import Machine


class HiveHelper:
    """Class for performing Hive related operations on Hadoop cluster using Hadoop client."""

    def __init__(self, commcell, client, connection_string, hdfs_user='hdfs', hive_user='hive'):
        """
        Initialising hive helper object
        Args:
            commcell                    (obj)  -- Commcell object
            client                      (str)  -- Client name of hive node
            connection_string           (str)  -- JDBC string used for hive connections
            hdfs_user                   (str)  -- hadoop user for executing hadoop related commands
            hive_user                   (str)  -- hive user for executing hive related commands
        Return:
            object - instance of this class
        """
        self.commcell = commcell
        self.client_machine = Machine(machine_name=client, commcell_object=self.commcell,
                                      hdfs_user=hdfs_user)
        self.controller_machine = Machine()
        self.connection_string = connection_string
        self.hdfs_user = hdfs_user
        self.hive_user = hive_user
        self.fake = Faker()
        self.log = logger.get_log()
        self.__init_kinit()

    def __init_kinit(self):
        """Runs kinit for hdfs & hive principal using keytab file specified in hdfs-site.xml"""
        if "principal" in self.connection_string:
            kinit_cache = "hdfs getconf -confkey hadoop.user.keytab.file"
            keytab_file = self.__run_command(kinit_cache).formatted_output
            kinit_hdfs = f"sudo -u {self.hdfs_user} kinit -kt {keytab_file} hdfs"
            self.__run_command(kinit_hdfs)
            kinit_hive = f"sudo -u {self.hive_user} kinit -kt {keytab_file} hive"
            self.__run_command(kinit_hive)
            kinit_cache = "hdfs getconf -confkey hive.user.keytab.file"
            keytab_file = self.__run_command(kinit_cache).formatted_output
            awk = "awk {\'print $NF\'}"
            fetch_kinituser = f"klist -kt {keytab_file} | grep -v  \"{keytab_file}\" | grep -w \"" \
                              f"{self.hive_user}\" | {awk} | sort | uniq | head -1"
            kinit_user = self.__run_command(fetch_kinituser).formatted_output
            kinit_hive = f"sudo -u {self.hive_user} kinit -kt {keytab_file} {kinit_user}"
            self.__run_command(kinit_hive)
            self.log.info('Kinit is successful.')
        else:
            self.log.info(f"Kerberos is not enabled on cluster or please reinitialize using "
                          f"correct JDBC connection string, entered JDBC: {self.connection_string}")

    def __run_command(self, command):
        """
        Runs a command on hive node
        Args:
            command             (str) -- command to be run on hive node
        Returns:
            client              (obj) -- returns command output object
        Raises:
            Exception:
                If non beeline command failed to execute.
        """
        cmd_out = self.client_machine.execute_command(command)
        if cmd_out.exit_code != 0 and 'beeline' not in command:
            excp = f"\nexitcode: {cmd_out.exit_code}," \
                   f"\n output: {cmd_out.output},\n error: {cmd_out.exception}\n"
            raise Exception(f"Command: {command}\nException: {excp}")
        return cmd_out

    @staticmethod
    def __parse_query_output(output, parse_as_string=False):
        """
        Parses the beeline query output by removing unnecessary symbols/details
        Args:
            output              (str)      -- Output of a beeline command
            parse_as_string     (bool)     -- Determines whether to parse output as string/list
        Returns:
            parsed_output             (str/list) -- returns parsed string/list
        Raises:
            Exception:
                If non beeline command failed to execute.
        """
        beelinelist = []
        for line in output.split('\n'):
            if "+-" in line or "WARN" in line or line == "":
                continue
            beelinelist.append(line.replace("|", "").strip())
        return " ".join(beelinelist[1:]) if parse_as_string else beelinelist[1:]

    def __run_query(self, query, list_parse=False, string_parse=False):
        """
        Executes the query using beeline and returns the output
        Args:
            query               (str)      -- Query to be executed using beeline
            list_parse          (bool)     -- Determines if output needs to be parsed as list
            string_parse        (bool)     -- Determines if output needs to be parsed as string
        Returns:
            output              (str/list) -- Output of the beeline query
        Raises:
            Exception:
                If non beeline query failed with non resolvable/ignorable errors.
        """
        command = f"sudo -u {self.hive_user} beeline --silent=true -u '{self.connection_string}' " \
                  f"-n {self.hive_user} -e \"{query}\""
        cmd_out = self.__run_command(command)
        if cmd_out.exit_code:
            resolvable_errors = ['Error communicating with the metastore', 'Unable to instantiate',
                                 'Failed to open new session']
            ignorable_errors = ["cannot be declared transactional because it's an external table",
                                'The table must be stored using an ACID compliant']
            error = cmd_out.exception.split('Error:')[-1].split('Closing:')[0]
            if any(_ in cmd_out.exception for _ in resolvable_errors):
                self.log.info(f"error:{error}")
                self.log.info("Trying to resolve error")
                if 'GSS initiate failed' in cmd_out.exception:
                    self.__init_kinit()
                else:
                    time.sleep(20)
                return self.__run_query(query, list_parse, string_parse)
            if any(_ in cmd_out.exception for _ in ignorable_errors):
                self.log.info(f"Command Executed:{command}")
                self.log.info(f"Ignoring this due to an acceptable error:{error} for above "
                              f"command, proceeding with other commands")
            else:
                msg = cmd_out.exception_message
                if 'serviceDiscoveryMode=zooKeeper;zooKeeperNamespace=hiveserver2' in msg:
                    msg = ''
                else:
                    msg = f"\nmessage:{msg}"
                raise Exception(f"\nquery:{query}\nerror:{error}{msg}")
            return None
        if list_parse:
            return self.__parse_query_output(cmd_out.output)
        if string_parse:
            return self.__parse_query_output(cmd_out.output, True)
        return cmd_out.output

    def __list_databases(self, prefix=None):
        """
        List all the databases based on prefix
        Args:
            prefix              (str)      -- Prefix value of the database name
        Returns:
            output              (list)     -- list of databases with given prefix
        """
        query = 'show databases;'
        result = self.__run_query(query, list_parse=True)
        prefix = prefix or ''
        return [database for database in result if database.startswith(prefix)]

    def create_database(self, database, force=False):
        """
        Creates a database with given name
        Args:
            database      (str)      -- name of the database to be created
            force         (bool)     -- Determines if database needs to be dropped and recreated
        """
        if force:
            self.drop_database(database)
        query = f'CREATE DATABASE IF NOT EXISTS {database};'
        self.__run_query(query)

    def drop_database(self, database, force=True):
        """
        Drops the database with given name
        Args:
            database      (str)      -- name of the database to be created
            force         (bool)     -- Determines if tables in database needs to be dropped
        """
        if force:
            force = 'cascade'
        else:
            force = ''
        query = f'DROP DATABASE IF EXISTS {database} {force};'
        self.__run_query(query)
        if force == 'cascade':
            for table_space in ['managed', 'external']:
                command = f"sudo -u {self.hdfs_user} hdfs dfs -rm -r -f /warehouse/tablespace/" \
                          f"{table_space}/hive/{database}.db"
                self.__run_command(command)

    def _fetch_database_data(self, database, tables=None):
        """
        Fetches the table data for a given database/specified tables
        Args:
            database      (str)      -- name of the database
            tables        (list)     -- fetches data for specified tables in the database
        Returns:
            db_data       (dict)     -- key as table name and its value as table_data
        """
        db_data = {}
        if tables is None:
            tables = self.__list_tables(database, only_names=True)
        for table in tables:
            tbl_data = self.__fetch_table_data(table_identifier=f'{database}.{table}')
            db_data[table.lower()] = tbl_data
        return db_data

    def __list_tables(self, database='default', only_names=False, prefix=None, empty=False):
        """
        List all the tables in given database
        Args:
            database            (str)      -- name of the database
            only_names          (bool)     -- Determines if table_identifiers(db.tbl) to be returned
            prefix              (str)      -- prefix value of the table name
            empty               (bool)     -- Returns only empty tables if specified
        Returns:
            output              (list)     -- list of tables
        """
        if database is None:
            return []
        query = f'show tables in {database};'
        result = self.__run_query(query, list_parse=True)
        prefix = prefix or ''
        if empty:
            return [f"{database}.{table}" if not only_names else f"{table}" for table in result if
                    table.startswith(prefix) and self.__is_table_empty(f"{database}.{table}")]
        return [f"{database}.{table}" if not only_names else f"{table}" for table in result if
                table.startswith(prefix)]

    def __create_table(self, **kwargs):
        """
        Constructs a create query based on given arguments and executes it
        Args:
        kwargs                (dict)  --  dict of keyword arguments as follows
            table_identifier    (str)   -- name of the table (format - db.table)
                required input
            file_format         (str)   -- sequencefile/rcfile/orc/parquet/textfile/avro
                required input
            table_mode          (str)   -- EXTERNAL/MANAGED
                default - EXTERNAL
            no_of_columns       (int)   -- no_of_columns
                default - 4
            table_type          (str)   -- default/partition/bucket/partition_bucket
                default - default
            row_format          (str)   -- row format to be used
                default - based on file_format
                eg- 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
            serde_property      (str)   -- serde properties for table
                default - None
                eg- "'field.delim'=',','serialization.format'=','"
            table_property      (str)   -- additional table properties
                default - None
                eg- "'transactional'='true','transactional_properties'='insert_only'"
            location            (str)   -- table_path for the table
                default - None (hive decides the path based on table)
        """
        create_query = "CREATE"
        if kwargs.get("table_mode").upper() != "MANAGED":
            create_query += " EXTERNAL"
        create_query += f' TABLE IF NOT EXISTS {kwargs["table_identifier"]}'

        table_format = ['id int']
        for column in range(kwargs.get("no_of_columns", 4) - 1):
            table_format.append(f'col{column} string')

        row_format_map = {
            'sequencefile': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe',
            'rcfile': 'org.apache.hadoop.hive.serde2.columnar.LazyBinaryColumnarSerDe',
            'orc': 'org.apache.hadoop.hive.ql.io.orc.OrcSerde',
            'parquet': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
            'textfile': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe',
            'avro': 'org.apache.hadoop.hive.serde2.avro.AvroSerDe'
        }

        partitioned_by = f'PARTITIONED BY ({",".join(table_format[2:4])})'
        clustered_by = f'CLUSTERED BY (id) into {4} BUCKETS'
        row_format = "ROW FORMAT SERDE"
        if kwargs.get("row_format"):
            row_format += f' \'{kwargs.get("row_format")}\''
        else:
            row_format += f' \'{row_format_map.get(kwargs.get("file_format"))}\''
        if kwargs.get("serde_property"):
            row_format += f' WITH SERDEPROPERTIES ({kwargs.get("serde_property")})'
        stored_as = f'STORED AS {kwargs["file_format"]}'

        if kwargs.get('table_type') == "partition":
            create_query += f' ({",".join(table_format[0:2])}) {partitioned_by}'
        elif kwargs.get('table_type') == "bucket":
            create_query += f' ({",".join(table_format)}) {clustered_by}'
        elif kwargs.get('table_type') == "partition_bucket":
            create_query += f' ({",".join(table_format[0:2])}) {partitioned_by} {clustered_by}'
        else:
            create_query += f' ({",".join(table_format)})'
        create_query += f' {row_format} {stored_as}'
        if kwargs.get("location"):
            create_query += f' LOCATION \'{kwargs.get("location")}\''
        if kwargs.get("table_property"):
            create_query += f' TBLPROPERTIES ({kwargs.get("table_property")})'
        self.__run_query(create_query)

    def __drop_table(self, table_identifier):
        """
        Drops table if exists
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
        """
        query = f'DROP TABLE IF EXISTS {table_identifier};'
        self.__run_query(query)
        database, table = table_identifier.split('.')
        for table_space in ['managed', 'external']:
            command = f"sudo -u {self.hdfs_user} hdfs dfs -rm -r -f /warehouse/tablespace/" \
                      f"{table_space}/hive/{database}.db/{table}"
            self.__run_command(command)

    def __select_count(self, table_identifier):
        """
        Returns no of rows by running select command on table
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
        Returns:
            count               (int)   -- no of rows in the table
        """
        query = f"select * from {table_identifier}"
        return len(self.__run_query(query, list_parse=True))

    def __get_row_count(self, table_identifier):
        """
        Returns no of rows by running select/show tblproperties command on table
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
        Returns:
            count               (int)   -- no of rows in the table
        """
        query = f"show tblproperties {table_identifier}('numRows')"
        result = self.__run_query(query, string_parse=True)
        if 'does not' in result:
            row_count = self.__select_count(table_identifier)
        else:
            row_count = int(result.split()[0])
        return row_count

    def __describe_formatted_table(self, table_identifier):
        """
        Returns output of describe formatted command on table
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
        Returns:
            query_output        (list)  -- describe formatted command output
        """
        self.__analyze_table(table_identifier)
        query = f"describe formatted {table_identifier}"
        query_output = self.__run_query(query, list_parse=True)
        exclude_properties = ['Database', 'CreateTime', 'COLUMN_STATS_ACCURATE',
                              'last_modified_by', 'last_modified_time', 'transient_lastDdlTime',
                              "Location:", "numRows", "rawDataSize", 'Storage Desc Params:', 'serialization.format']
        for _ in exclude_properties:
            exclude = next(iter(list(filter(lambda x: x.startswith(_), query_output))), None)
            if exclude in query_output:
                query_output.remove(exclude)
        return query_output

    def __select_all_from_table(self, table_identifier):
        """
        Returns output of select all command on table
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
        Returns:
            query_output        (list)  -- select all command output
        """
        query = f"select * from {table_identifier}"
        result = self.__run_query(query, list_parse=True)
        if len(result) == 0:
            self.__repair_table(table_identifier)
            return sorted(self.__run_query(query, list_parse=True))
        return sorted(result)

    def __fetch_table_data(self, table_identifier):
        """
        Returns output of select all command on table
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
        Returns:
            table_data          (dict)  -- select all and describe formatted command outputs
        """
        self.log.info(f"Fetching table data for:{table_identifier}")
        table_data = {"select_query": self.__select_all_from_table(table_identifier),
                      'describe_formatted': self.__describe_formatted_table(table_identifier)}
        return table_data

    def __insert_into_table(self, table_identifier, no_of_rows=3, no_of_columns=4,
                            batch_insert=False, start_id=None):
        """
        Inserts data into given table
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
            no_of_rows          (int)   -- no of rows to be inserted
            no_of_columns       (int)   -- no of columns present in table
            batch_insert        (bool)  -- reinserts all rows from table on itself
                default - False
            start_id            (int)   -- beginning row id
                default - uses row count
        Returns:
            row_count           (int)  -- row id of last inserted row
        """
        row_count = start_id or self.__get_row_count(table_identifier)
        for row in range(no_of_rows):
            row_data = f"""{row_count + row + 1},{','.join(f"'{self.fake.word()}'"
                                                           for _ in range(no_of_columns - 1))}"""
            query = f'INSERT INTO table {table_identifier} VALUES ({row_data});'
            self.__run_query(query)
            row_count += 1
        if no_of_rows == 0:
            self.log.info("Skipping insert since number of rows to be inserted is zero")
        else:
            self.log.info(f"Data inserted into {table_identifier} successfully")
        if batch_insert:
            query = f'INSERT INTO table {table_identifier} select * from {table_identifier};'
            self.__run_query(query)
        return row_count

    def __update_table(self, table_identifier, row_id, value=None):
        """
        Updates row data in the table based on given row_id and value
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
            row_id              (int)   -- id of the row that needs updating
            value               (str)   -- value used for updating
                default  - updated
        """
        query = f"update {table_identifier} set col0=\'{value or 'updated'}\' where id={row_id};"
        self.__run_query(query)

    def __delete_from_table(self, table_identifier, row_id):
        """
        Deletes given row from the table
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
            row_id              (int)   -- id of the row that needs to be deleted
        """
        query = f"delete from {table_identifier} where id={row_id}"
        self.__run_query(query)

    def __acid_the_table(self, table_identifier, no_of_columns=4, no_of_acids=1):
        """
        Runs acid operations on given table
        Each acid operation consists of (4 inserts, 1 delete & 1 update).
        If it's not acid supported just inserts two rows of data.
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
            no_of_columns       (int)   -- no of columns present in table
                default - 4
            no_of_acids         (int)  -- no of acid operations to be performed
                default - 1
        """
        acid_supported = self.__is_table_transactional(table_identifier, acid_made=True)
        row_id = None
        for _ in range(no_of_acids):
            row_id = self.__insert_into_table(table_identifier, 1, no_of_columns, start_id=row_id)
            if acid_supported:
                row_id = self.__insert_into_table(table_identifier, 1, no_of_columns,
                                                  start_id=row_id)
                self.__delete_from_table(table_identifier, row_id=row_id)
                row_id = self.__insert_into_table(table_identifier, 1, no_of_columns,
                                                  start_id=row_id)
                self.__update_table(table_identifier, row_id=row_id)
            else:
                self.log.info(f"Table:{table_identifier} is not acid supported. Only inserting data")
            row_id = self.__insert_into_table(table_identifier, 1, no_of_columns, start_id=row_id)

    def __compact_the_table(self, table_identifier, compaction_type=None):
        """
        Runs compact operation on the given table
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
            compaction_type     (str)   -- minor/major
        """
        compaction_type = compaction_type or table_identifier.split('_')[-1]
        if compaction_type in ['minor', 'major'] and self.__is_table_transactional(
                table_identifier):
            if self.__is_table_partitioned(table_identifier):
                partition_col = self.__is_table_partitioned(table_identifier, get_partition=True)
                if partition_col:
                    partition_col = partition_col.replace('/', '\',').replace('=', '=\'')
                    partition_clause = f"partition ({partition_col}')"
                else:
                    partition_clause = None
            else:
                partition_clause = f""
            if partition_clause:
                query = f"ALTER TABLE {table_identifier} {partition_clause} COMPACT " \
                        f"'{compaction_type}'"
                self.__run_query(query)
            else:
                self.log.info(
                    f"cannot run compaction on partitioned table:{table_identifier} without any "
                    f"partition columns")
        else:
            self.log.info(f"Skipping compaction wrong property:{compaction_type} specified")

    def __is_table_exists(self, table_identifier):
        """
        Checks if table exists
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
        Returns:
            bool  -- True if table exists else False
        """
        database, tbl = table_identifier.split('.')
        query = f"use {database}; show tables like '{tbl}';"
        result = self.__run_query(query, list_parse=True)
        return tbl in result

    def __is_table_empty(self, table_identifier):
        """
        Checks if table is empty
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
        Returns:
            bool  -- True if table is empty else False
        """
        query = f'select * from {table_identifier} limit 1;'
        query_result = self.__run_query(query, list_parse=True)
        is_empty = True
        if query_result and 'NULL' not in query_result:
            is_empty = False
        return is_empty

    def __is_table_transactional(self, table_identifier, acid_made=False):
        """
        Checks if table is transactional/acid supported
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
            acid_made           (bool)  -- Determines if table is acid supported or not
        Returns:
            bool  -- True if table is acid supported/transactional else False
        """
        query = f"show tblproperties {table_identifier}('transactional')"
        result = self.__run_query(query, string_parse=True)
        if 'does not' in result:
            return False
        if acid_made:
            query = f"show tblproperties {table_identifier}('transactional_properties')"
            result = self.__run_query(query, string_parse=True)
            if 'does not' in result or 'default' not in result:
                return False
        return True

    def __is_table_partitioned(self, table_identifier, get_partition=False):
        """
        Checks if table is partitioned
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
            get_partition       (bool)  -- Determines if table is partitioned and returns partition
        Returns:
            bool/string  -- True/partition if table is partitioned else False
        """
        if "partition" in table_identifier:
            if get_partition:
                query = f"show partitions {table_identifier};"
                partition = self.__run_query(query, list_parse=True)
                if len(partition) != 0:
                    return partition[len(partition) // 2]
                return False
            return True
        return False

    def __analyze_table(self, table_identifier):
        """
        Runs analyze command on table
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
        """
        query = f"analyze table {table_identifier} compute statistics noscan;"
        self.__run_query(query)

    def __repair_table(self, table_identifier):
        """
        Runs repair command on table
        Args:
            table_identifier    (str)   -- name of the table (format - db.table)
        """
        query = f'Msck repair table {table_identifier};'
        self.__run_query(query)

    def __create_directory(self, location=None, owner='hive'):
        """
        Creates a directory in hdfs and runs chown command with given owner
        Args:
            location            (str)   -- directory to be created
                default - /hive_automation_test_loc
            owner               (str)   -- owner for the created hdfs directory
                default - hive
        Returns:
            str     -   location of created hdfs directory
        """
        location = location or '/hive_automation_test_loc'
        cmd = f"sudo -u {self.hdfs_user} hdfs dfs -mkdir -p {location}"
        self.__run_command(cmd)
        cmd = f"sudo -u {self.hdfs_user} hdfs dfs -chown {owner} {location}"
        self.__run_command(cmd)
        return location

    def generate_test_data(self, no_of_acids=2, no_of_columns=4, database=None, force_insert=False,
                           table_modes=None, location=None, row_format=None,
                           file_formats=None, table_types=None, serde_properties=None,
                           table_properties=None, fetch_data=False):
        """
        Creates tables in specified database and generates data into table
        Args:
            no_of_acids         (int)      -- no of acid operations to be performed
                default - 2
            no_of_columns       (int)      -- no of columns present in table
                default - 4
            database            (str)      -- name of the database
                default - autodb
            force_insert        (bool)     -- if force insert has to be made
                default - False
            table_modes         (list)     -- [MANAGED]
                default - [EXTERNAL, MANAGED]
            location            (str)      -- table_path for the table
                default - None (hive decides the path based on table)
            row_format          (str)      -- row format to be used
                default - based on file_format
            file_formats        (list)     -- [orc,textfile]
                default - ['sequencefile', 'rcfile', 'orc', 'parquet', 'textfile', 'avro']
            table_types         (list)     -- [default,partition_bucket]
                default - ['default', 'partition', 'bucket', 'partition_bucket']
            serde_properties    (list)     -- strings list, each string - one set of serde property
                default - None If True is sent, uses known and problematic serde properties
                eg- ["'field.delim'=',','serialization.format'=','"]
            table_properties    (list)    -- additional list table properties
                default - None
                eg- ["'transactional'='true','transactional_properties'='insert_only'"]
            fetch_data          (bool)    -- fetches generated database data
        Returns:
            dict - {} if fetch data is false else dict having table names and its data as k,v pairs
        """
        generated_databases = []
        if table_types is None:
            table_types = ['default', 'partition', 'bucket', 'partition_bucket']
        if file_formats is None:
            file_formats = ['sequencefile', 'rcfile', 'orc', 'parquet', 'textfile', 'avro']
        if table_modes is None:
            table_modes = ['managed', 'external']
        if serde_properties is None:
            serde_properties = []
        elif serde_properties is True:
            serde_properties = ["'field.delim'=',','serialization.format'=','",
                                "'field.delim'='~*'",
                                '\'escapeChar\'=\'\\\\\\\\\',\'quoteChar\'=\'\\"\',\'separatorChar\'=\',\'',
                                "'field.delim'='\\;', 'serialization.format'='\\;'",
                                "'input.regex'='^(\\d+)~\\*(.*)$'",
                                "'field.delim'='59', 'serialization.format'='59'"]
        compact_modes = None
        if table_properties is None:
            table_properties = []
        elif isinstance(table_properties, dict):
            table_props = []
            transactional_modes = table_properties.get('transactional_modes', [])
            if transactional_modes is True:
                transactional_modes = ['true', 'false']
            transactional_properties = table_properties.get('transactional_properties', [])
            if transactional_properties is True:
                transactional_properties = ['default', 'insert_only']
            compact_modes = table_properties.get('compact_modes', [])
            if compact_modes is True:
                compact_modes = ['major', 'minor', 'autocompact', 'nocompact']
            if compact_modes:
                transactional_modes = ['true']  # compaction doesn't work for non transactional tables
                transactional_properties = transactional_properties or ['default', 'insert_only']
            table_props.append([f"'transactional'='{_}'" for _ in transactional_modes])
            table_props.append(
                [f"'transactional_properties'='{_}'" for _ in transactional_properties])
            while [] in table_props:
                table_props.remove([])
            table_properties = [','.join(i) for i in list(itertools.product(*table_props))]
        unsupported_tblprop = "'transactional'='false','transactional_properties'='insert_only'"
        if unsupported_tblprop in table_properties:
            table_properties.remove(unsupported_tblprop)  # removed since it doesn't work
        db_prefix = None
        if not database:
            db_prefix = "automationdb_"
            for file_format in file_formats:
                database = f"{db_prefix}{file_format}".lower()
                self.create_database(database)
                generated_databases.append(database.lower())
        else:
            self.create_database(database)
            generated_databases.append(database.lower())
        if location:
            self.__create_directory(location)
        for table_mode in table_modes:
            if table_mode == 'table_space':
                table_space = 'end'
                location = self.__create_directory(location)
            else:
                table_space = table_mode[0:3]
            for file_format in file_formats:
                for table_type in table_types:
                    temp_serde_properties = copy.deepcopy(serde_properties)
                    while True:
                        serde_name = f'serde{len(temp_serde_properties)}'
                        if temp_serde_properties:
                            serde_property = temp_serde_properties.pop()
                        else:
                            serde_property = None
                        temp_table_properties = copy.deepcopy(table_properties)
                        while True:
                            tblprop_name = f'tblprop{len(temp_table_properties)}'
                            if temp_table_properties:
                                table_property = temp_table_properties.pop()
                            else:
                                table_property = None
                            temp_compact_modes = copy.deepcopy(compact_modes)

                            while True:
                                if temp_compact_modes:
                                    compact_mode = temp_compact_modes.pop()
                                else:
                                    compact_mode = 'defcompact'
                                table_name = f'{table_space}_{file_format}_{table_type}' \
                                             f'_{serde_name}_{tblprop_name}_{compact_mode}'
                                if db_prefix:
                                    table_identifier = f'{f"{db_prefix}{file_format}"}.{table_name}'
                                else:
                                    table_identifier = f'{database.lower()}.{table_name}'
                                table_path = None
                                if location:
                                    table_path = f'{location}/{table_name}'
                                temp_table_property = table_property
                                if compact_mode != "defcompact":
                                    comp_prop = 'false' if compact_mode == 'autocompact' else 'true'
                                    compact_property = f"'NO_AUTO_COMPACTION'='{comp_prop}'"
                                    table_property = f"{table_property}, {compact_property}"
                                table_options = {"table_mode": table_mode,
                                                 "table_identifier": table_identifier,
                                                 "no_of_columns": no_of_columns,
                                                 "table_type": table_type,
                                                 "row_format": row_format,
                                                 "serde_property": serde_property,
                                                 "file_format": file_format,
                                                 "location": table_path,
                                                 "table_property": table_property}
                                self.__create_table(**table_options)
                                if no_of_acids != 0 and self.__is_table_exists(table_identifier) \
                                        and (force_insert or self.__is_table_empty(table_identifier)):
                                    self.log.info(f"Generating test data for table:{table_identifier}")
                                    self.__acid_the_table(table_identifier, no_of_columns, no_of_acids)
                                table_property = temp_table_property

                                if not temp_compact_modes:
                                    break
                            if not temp_table_properties:
                                break
                        if not temp_serde_properties:
                            break
        test_data = {}
        if fetch_data:
            test_data = {db: self._fetch_database_data(db) for db in generated_databases}
        return test_data

    def validate_test_data(self, database_map, backupdata=None, restoredata=None):
        """"
        Validates source and destination table data
        Args:
            database_map        (dict)    -- contains restore db as key and source db as value
            backupdata          (dict)    -- backup/source database data
                default - None fetches source db data
            restoredata         (dict)    -- restore/destination database data
                default - None fetches destination db data
        Raises:
            Exception:
                If validation failed for any of the table.
        """
        sourcedb_data = backupdata or {db: self._fetch_database_data(db) for db in
                                       database_map.values()}
        if restoredata is not None:
            destinationdb_data = {db: self._fetch_database_data(db, tables=restoredata.get(db))
                                  for db in restoredata.keys()}
        else:
            destinationdb_data = {db: self._fetch_database_data(db) for db in database_map.keys()}
        for restoredb in database_map:
            database = destinationdb_data[restoredb]
            for table in database:
                table_pdict = {f"src_{table}": {}, f"dest_{table}": {}}
                for table_data in database[table]:
                    src_tbl_data = sourcedb_data[database_map[restoredb]][table][table_data]
                    res_tbl_data = database[table][table_data]

                    if res_tbl_data == src_tbl_data:
                        self.log.info(f'{table_data} Validation successfully for {table}')
                        table_pdict[f"src_{table}"].update({f"{table_data}": "Matched"})
                        table_pdict[f"dest_{table}"].update({f"{table_data}": "Matched"})
                    else:
                        diff = {f"src_{table_data}": [x for x in src_tbl_data if x not in
                                                      res_tbl_data],
                                f"dest_{table_data}": [x for x in res_tbl_data if x not in
                                                       src_tbl_data]}
                        self.log.info(f"{table_data} Validation Failed for {table}")
                        self.log.info(f"Different Entities for {table} are: {diff}")
                        if table_data == "describe_formatted":
                            try:
                                table_pdict[f"src_{table}"].update(
                                    dict(" ".join(((x.replace("NULL", '')).replace(
                                        "Table Type:", "Table_Type:")).split()).split(" ") for x in
                                         diff[f"src_{table_data}"]))
                                table_pdict[f"dest_{table}"].update(
                                    dict(" ".join(((x.replace("NULL", '')).replace(
                                        "Table Type:", "Table_Type:")).split()).split(" ") for x in
                                         diff[f"dest_{table_data}"]))
                            except Exception as excp:
                                self.log.info(f"Skipping describe formatted table validation due to error: {excp}")
                                continue
                        else:
                            table_pdict[f"src_{table}"].update(
                                {f"{table_data}": diff[f"src_{table_data}"]})
                            table_pdict[f"dest_{table}"].update(
                                {f"{table_data}": diff[f"dest_{table_data}"]})
                            raise Exception(f"Validation Failed for {table}, source"
                                            f":{src_tbl_data} and destination:{res_tbl_data}")
                temp_time = datetime.now().strftime("%d_%m_%Y_%I_%M_%p")
                csv_file_path = f'diff_{restoredb}__{database_map[restoredb]}_{temp_time}.csv'
                csv_file_path = self.controller_machine.join_path(
                    self.controller_machine.tmp_dir, csv_file_path)
                pd.DataFrame(table_pdict).to_csv(csv_file_path, mode='a')
            src_tbl = self.__list_tables(database_map.get(restoredb), only_names=True)
            res_tbl = self.__list_tables(restoredb, only_names=True)
            if src_tbl != res_tbl:
                raise Exception(f'Tables not matched. source table list:{src_tbl} destination table list:{res_tbl}')
            else:
                self.log.info("All source tables are backed up and restored successfully")

    def acid_the_tables(self, database=None, table_identifiers=None, no_of_acids=1, no_of_columns=4):
        """
        Runs acid operations on given list of table identifiers
        Args:
            database            (str)   -- name of the database
            table_identifiers   (list)  -- list of the table identifiers (format - [db.table])
            no_of_acids         (int)  -- no of acid operations to be performed
            no_of_columns       (int)   -- no of columns present in table
        Raises:
            Exception:
                If database or table_identifiers is not sent
        """
        if database is None and table_identifiers is None:
            raise Exception("Database or table_identifiers is a required input")
        table_identifiers = table_identifiers or []
        table_identifiers.extend(self.__list_tables(database))
        for table_identifier in table_identifiers:
            self.__acid_the_table(table_identifier, no_of_columns, no_of_acids)

    def insert_into_tables(self, database=None, table_identifiers=None, force_insert=False, no_of_rows=3, no_of_columns=4):
        """
        Inserts data into list of table_identifiers or given database
        Args:
            database            (str)   -- name of the database
            table_identifiers   (list)  -- list of the table identifiers (format - [db.table])
            force_insert        (bool)  -- if force insert has to be made
                default - False
            no_of_rows          (int)   -- no of rows to be inserted
            no_of_columns       (int)   -- no of columns present in table
        Raises:
            Exception:
                If database or table_identifiers is not sent
        """
        if database is None and table_identifiers is None:
            raise Exception("Database or table_identifiers is a required input")
        table_identifiers = table_identifiers or []
        table_identifiers.extend(self.__list_tables(database))
        for table_identifier in table_identifiers:
            if force_insert or self.__is_table_empty(table_identifier):
                self.__insert_into_table(table_identifier, no_of_rows, no_of_columns)

    def get_tables(self, databases):
        """
        Returns list of table_identifiers from given list of databases
        Args:
            databases           (list)  -- list of the databases
        Returns:
            list    -   list of the table identifiers (format - [db.table])
        """
        table_identifiers = []
        for database in databases:
            table_identifiers.extend(self.__list_tables(database))
        return table_identifiers

    def drop_tables(self, database=None, table_identifiers=None, contains=None):
        """
        Drops list of table_identifiers or given database based on contains value
        Args:
            database            (str)   -- name of the database
            table_identifiers   (list)  -- list of the table identifiers (format - [db.table])
            contains            (str)   -- drops table if this value is present in table identifier name
        Returns:
            list     -   list of dropped table_identifiers (format - [db.table])
        Raises:
            Exception:
                If database or table_identifiers is not sent
        """
        if database is None and table_identifiers is None:
            raise Exception("Database or table_identifiers is a required input")
        table_identifiers = table_identifiers or []
        table_identifiers.extend(self.__list_tables(database))
        dropped_tables = []
        for table_identifier in table_identifiers:
            if contains is not None:
                if contains not in table_identifier:
                    continue
            self.__drop_table(table_identifier)
            dropped_tables.append(table_identifier)
        return dropped_tables
