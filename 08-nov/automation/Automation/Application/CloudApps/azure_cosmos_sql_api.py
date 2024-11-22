# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing operations on Azure Cosmos Database using
Azure SDK for python
===========================================================================

CosmosSQLAPI:
-------------------
    __init__            --  Initializes the CosmosSQLAPI instance using URI and key
    
    create_database()   --  Creates CosmosDB database
    
    get_db_client()     --  Returns the object of database class to perform operations
    
                            on CosmosDB database
    
    delete_database()   --  Deletes the given database
    
    create_container()  --  Creates CosmosDB container under given database
    
    get_cnt_client()    --  Returns the object of container class to invoke operations
    
                            on CosmosDB container
    
    populate_container() -- Populates the given container with test data
    
    delete_container()   -- Deletes the container under given database
    
    validate_container() -- Validates the items in the container after restore

CosmosCassandraAPI:
-------------------
    __init__            --  Initializes the CosmosCasandraAPI instance 
    
    connection()        --  Return CosmosDB Cassandra API database connection
    
    disconnect()        --  Disconnect the CosmosDB cassandra API instnace connection
    
    create_keyspace()   --  Create keyspace
    
    drop_keyspace()     --  Drop keyspace
    
    create_table()      --  Create table
    
    drop_table()        --  Drop table
    
    truncate_table()    --  Truncate table
    
    add_test_data()     --  Populate test data
    
    update_test_data()  --  Update existin test data
    
    get_rows()          --  Get table rows ResultSet
"""

import time
from azure.cosmos import cosmos_client
from azure.cosmos import PartitionKey
from AutomationUtils import logger
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, ResultSet
from ssl import PROTOCOL_TLSv1_2, SSLContext, CERT_NONE


class CosmosSQLAPI:
    """Helper class to interact with Azure CosmosDB SQL API
        using Azure SDK for python"""
    def __init__(self, account_uri, account_key):
        """Initializes the CosmosDB account URL, key and Instantiates Cosmos client class
        Args:
        account_uri:    (str): The URI of CosmosDB account to connect to

        account_key:    (str): The primary master key of the CosmosDB account
        """
        self.account_uri = account_uri
        self.account_key = account_key
        self.client = cosmos_client.CosmosClient(self.account_uri, self.account_key)
        self.log = logger.get_log()

    def create_database(self, database_name, throughput=0):
        """Creates CosmosDB database
        Args:
            database_name:  (str)   --  Name of database

            throughput:     (int)   --  Throughput to be assigned
                default- 0

        Raises:
            Exception:  If database could not be created due to CosmosDB issue
                        Account URI or key is not valid
        """
        try:
            databases = list(self.client.list_databases())
            for database in databases:
                if database_name == database.get('id'):
                    self.log.info('Database with name %s exists, deleting and recreating it',
                                  database_name)
                    self.delete_database(database_name)
            if throughput == 0:
                self.client.create_database(id=database_name)
            else:
                self.client.create_database(id=database_name, offer_throughput=throughput)
            self.log.info('Database created successfully')

        except Exception as exp:
            self.log.exception('Creating database failed with error: %s', exp)

    def get_db_client(self, database_name):
        """Returns the object of database class to perform operations on CosmosDB database
        Args:
            database_name:  (str)   --  Name of database

        Raises:
            Exception:
                If database with given name does not exist
        """
        try:
            return self.client.get_database_client(database_name)
        except Exception as exp:
            self.log.exception("Database doesn't exist or not able to return object: %s", exp)
            raise exp

    def delete_database(self, database_name):
        """Deletes the database
        Args:
            database_name:  (str)   --  Name of database

        Raises:
            Exception:
                If database with given name does not exist
                Database could not be deleted due to CosmosDB issue
        """
        try:
            self.client.delete_database(database_name)
            self.log.info("database deleted successfully")
        except Exception as exp:
            self.log.exception("delete database failed with error: %s", exp)
            raise exp

    def create_container(self, database_name, container_name, partition_key, throughput=0):
        """Creates a CosmosDB container with given attributes
        Args:
            database_name:  (str)   --  Name of database

            container_name  (str)   --  Name of container

            partition_key   (str)   -- Name of the partition key column

            throughput      (int)   --  Throughput to be assigned

        Raises:
            Exception:
                If database doesnt exist
                invalid throughput value is provided
                container could not be created due to CosmosDB issue
        """
        try:
            containers = list(self.get_db_client(database_name).list_containers())
            for container in containers:
                if container_name in container.get('id'):
                    self.log.info('Database with name %s exists, '
                                  'deleting and recreating it', container_name)
                    self.delete_container(container_name, database_name)
            if throughput > 0:
                self.get_db_client(database_name).create_container(
                    id=container_name, partition_key=PartitionKey(path="/"+partition_key),
                    offer_throughput=throughput)
            else:
                self.get_db_client(database_name).create_container(
                    id=container_name,
                    partition_key=PartitionKey(path="/"+partition_key))
            self.log.info("Container created successfully")
        except Exception as exp:
            self.log.exception("Create container failed with error: %s", exp)
            raise exp

    def get_cnt_client(self, database_name, container_name):
        """Returns the object of container class to perform operations on CosmosDB container
        Args:
            database_name:  (str)   --  Name of database

            container_name  (str)   --   Name of container

        Returns:
            The object of the container class for given container

        Raises:
            Exception:
                If database does not exist
                If container does not exist
        """
        try:
            return self.get_db_client(
                database_name).get_container_client(container_name)
        except Exception as exp:
            self.log.exception("Container doesnt exist or not able to return object:%s", exp)
            raise exp

    def populate_container(self, database_name, container_name, partition_key,
                           num_items, start=1):
        """Populates the given container with test data
        Args:
            database_name:  (str)   --  Name of database

            container_name  (str)   --  Name of container

            partition_key   (str)   --  The name of the partition key column

            num_items       (int)   --  The number of items to populate

            start           (int)   --  The item/row number to start populating
                default is 1

        Raises:
            Exception:
                Non existing database or container name is passed
                Container could not be populate due to CosmosDB issue
        """
        try:
            container_client = self.get_cnt_client(database_name, container_name)
            for i in range(start, start+num_items):
                container_client.upsert_item({
                    "id": str(i),
                    'item': 'item' + str(i),
                    'timestamp': time.time(),
                    'description': 'CV AUTOMATION TESTCASE',
                    partition_key: i
                })
            self.log.info("Container populated successfully")
        except Exception as exp:
            self.log.exception("Error when populating container:%s", exp)
            raise exp

    def delete_container(self, database_name, container_name):
        """Deletes the container under given database
        Args:
            database_name:  (str)   --  Name of database

            container_name  (str)   --  Name of container
        Raises:
            Exception:
                Non existing database or container name is provided
                Container could not be deleted due to CosmosDB issue
        """
        try:
            self.get_db_client(database_name).delete_container(container_name)
            self.log.info("Container deleted successfully")
        except Exception as exp:
            self.log.exception("delete container failed with error: %s", exp)
            raise exp

    def validate_container(self, database_name, container_name, partition_key,
                           expected_count, start=1):
        """Validates the items in the container after restore
        Args:
            database_name:  (str)   --  Name of database

            container_name  (str)   --  Name of container

            partition_key   (str)   --  The name of the partition key column

            expected_count  (int)   --  The count of items on source

            start           (int)   --  The item/row number to start validating
                default is 1

        Raises:
            Exception:
                Non existing database or container name is passed
                If items in container could not be read due to CosmosDB issue
        """
        try:
            container_client = self.get_cnt_client(database_name, container_name)
            for item in container_client.query_items(
                    query=f'SELECT * FROM {container_name} c order by c.{partition_key}',
                    enable_cross_partition_query=True):
                if(item.get(partition_key) == start and item.get('item') == 'item'+str(start)
                        and item.get('description') == 'CV AUTOMATION TESTCASE'):
                    start += 1
                else:
                    raise Exception("Container validation failed, did not find expected items")
            if start != expected_count+1:
                raise Exception("Item count is not matching after restore")
            self.log.info("Container validated successfully")
        except Exception as exp:
            self.log.exception("Validating container failed with error: %s", exp)
            raise exp


class CosmosCassandraAPI:
    """Class which establishes connection with Cosmos DB cassandra API account
    and performs DB operations.
    """

    def __init__(self, cloudaccount, cloudaccount_password, port=10350):
        """ Initialize CosmosDBCassandraAPIHelper object.

        Args:
            port               (int) -- master node port number
            cloudaccount       (str) -- cloud account name
            cloud account_password    (str) -- cloud account password
        Return:
            object - instance of this class
        """
        self.contact_point = cloudaccount + ".cassandra.cosmos.azure.com"
        self.password = cloudaccount_password
        self.ssl_context = SSLContext(PROTOCOL_TLSv1_2)
        self.ssl_context.verify_mode = CERT_NONE
        self.auth_provider = PlainTextAuthProvider(
            username=cloudaccount, password=cloudaccount_password)
        self.port = port
        self.log = logger.get_log()
        self._connection = None
        self._connect()
        self.error_code = {}
        self.__error_code()
        self.log.info("Initialised cosmos DB cassandra API helper object")

    def __error_code(self):
        """dictionary of error codes"""
        error_code = {
            "-1": "Successful",
            "8704": "The query is correct but an invalid syntax.",
            "8192": "The submitted query has a syntax error. Review your query.",
            "8960": "The query is invalid because of some configuration issue. eg, try to drop non-exist keyspace",
            "8448": "Forbidden response, the user might have the necessary permissions to perform the request.",
            "0": "Server-side cassandra error. Please open a support ticket.",
            "4608": "Timeout during a read request.",
            "4352": "Timeout exception during a write serviceRequest.",
            "9216": "Attempting to create a keyspace or table that already exist.",
            "5376": "Precondition failure. A non-timeout write request exception is returned.",
            "4097": "Overload exception, Probably need more RU to handle the higher volume request.",
            "4096": "Service unavailable.",
            "256 ": "invalid connection credentials. Please check your connection credentials.",
            "10": "A client message triggered protocol violation."
        }
        self.error_code.update(error_code)

    def _connect(self):
        """Establish connection with the master node of the replica set or sharded cluster."""
        try:
            self.cluster = Cluster([self.contact_point],
                                   port=self.port,
                                   auth_provider=self.auth_provider,
                                   ssl_context=self.ssl_context)
            connection = self.cluster.connect()
            self.log.info("Connection established")
        except Exception as excp:
            raise Exception(
                'Failed to connect to the cassandra Server\nError: "{0}"'.format(excp))
        if connection is not None:
            self._connection = connection

    def __execute_command(self, query, values=None):
        try:
            self._connection.execute(query, values)
        except Exception as exception:
            if str(exception.error_code) in self.error_code:
                print(self.error_code[str(exception.error_code)])
            else:
                raise Exception(
                    'Failed to execute query \nError: "{0}"'.format(exception))

    @property
    def connection(self):
        """ Return the connection object established with the master node of the replica set."""
        return self._connection

    def disconnect(self):
        """shutdown the connection"""
        self.cluster.shutdown()

    def create_keyspace(self, keyspacename):
        """create keyspace
        Args:
            keyspacename (str)      -- keyspace name
        """
        cmd = f'CREATE KEYSPACE IF NOT EXISTS {keyspacename} WITH replication = ' + \
            '{\'class\': \'NetworkTopologyStrategy\', \'datacenter\' : \'1\' }'
        self.__execute_command(cmd)

    def drop_keyspace(self, keyspacename):
        """Drop keyspace
        Args:
            keyspacename (str)      -- keyspace name
        """
        cmd = f'DROP KEYSPACE {keyspacename}'
        self.__execute_command(cmd)

    def create_table(self, keyspacename, tablename):
        """create table
        Args:
            keyspacename (str)      -- keyspace name
            tablename (str)        -- table name
        """
        cmd = f'CREATE TABLE IF NOT EXISTS {keyspacename}.{tablename}' + \
            '(user_id int PRIMARY KEY, user_name text, user_bcity text)' + \
            'WITH cosmosdb_provisioned_throughput=400'
        self.__execute_command(cmd)

    def drop_table(self, keyspacename, tablename):
        """Drop table
        Args:
            keyspacename (str)      -- keyspace name
            tablename (str)        -- table name
        """
        cmd = f'DROP TABLE {keyspacename}.{tablename}'
        self.__execute_command(cmd)

    def truncate_table(self, keyspacename, tablename):
        """truncate table
        Args:
            keyspacename (str)      -- keyspace name
            tablename (str)        -- table name
        """
        cmd = 'TRUNCATE TABLE {keyspacename}.{tablename}'
        self.__execute_command(cmd)

    def add_test_data(self, keyspacename, tablename, user_ids):
        """insert data into keyspacename.tables
        Args:
            keyspacename (str)      -- keyspace name
            tablename (str)        -- table name
            user_ids (list)    -- user id list
        """
        for id in user_ids:
            cmd = f'INSERT INTO {keyspacename}.{tablename}  (user_id, user_name, ' + \
                'user_bcity) VALUES (%s,%s,%s)'
            values = [id, "test" + str(id), "city" + str(id)]
            self.__execute_command(cmd, values)

    def update_test_data(self, keyspacename, tablename, user_ids):
        """update existing test data
        Args:
            keyspacename (str)      -- keyspace name
            tablename (str)        -- table name
            user_ids (list)    -- user id list
        """
        for id in user_ids:
            cmd = f'UPDATE {keyspacename}.{tablename} SET user_name=modify{id}, ' + \
                'user_bcity=modify{id} where user_id={id}'
            self.__execute_command(cmd)

    def get_rows(self, keyspacename, tablename):
        """
        get rows ResultSet from table under keyspace
        Args:
            keyspacename (str)        -- keyspace name
            tablename (str)         -- table name
        Return:
            ResultSets for rows in table
        """
        try:
            cmd = f'SELECT user_id, user_name, user_bcity FROM {keyspacename}.{tablename}'
            rows = self._connection.execute(cmd)
            return list(rows)
        except Exception:
            raise Exception("failed to get table rows")


