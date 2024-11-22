# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing MongoDB operations.

Classes defined in this file
     MongoDBHelper : Class which connects to the master node of the cluster/ primary node
      of the replica set and performs MongoDB specific operations

         __int__ :Constructor for MongoDBHelper class,
          which creates connection to the replica set/sharded cluster

         __enter__:Returns the current instance

         __exit__:Closes the database connection if exists

         __del__:Closes the database connection if exists

         close_connection: Closes the database connection

         connection: Establishes the database connection

         _connect:Establishes connection to the replica set/sharded cluster

         __create_db:Creates a database in the sharded cluster/replica set

         __drop_db:Drops a database in the sharded cluster/replica set

         __check_if_db_exists:Checks if the database exists in the server

         __get_db_list:Returns the list of database in the replica set/sharded cluster

         __create_collection:Creates a collection in the specified database with specified name

         __count_documents_in_collection:count number of documents in a specified collection

         __get_collection_list:Returns the list of collections in the specified database

         generate_test_data:Generates test data for validation

         shutdown_mongodb_server:shutdown mongoDB server which has authentication enabled

         check_shardedcluster_or_replicaset:Check if MongoDB server in considration
         is a replica set/sharded cluster

         get_db_server_size:Returns MongoDB server size

         shutdown_server_using_kill_command:Shutdown MongoDB
         server which has authentication disabled

         get_replicaset_or_shardedcluster:check if MongoDB configuration
         is a replica set or sharded cluster from discovered table

         __checkForServer:Get MongoDB server information

         __get_mongodbassociationdetails_from_csdb: Get details about the MongoDB
         sharded cluster/replica set from CS DB post discovery of nodes

         shutdown_server_and_cleanup_using_command:Shutdown MongoDB
         nodes of a sharded cluster/replica set
         and cleanup the DB path when authentication is enabled

         validate_discovery_of_nodes:Validate discovery of nodes

         get_mongod_start_command_from_csdb: Get mongod start command of the nodes from the CSDB

         get_mongos_start_command_from_csdb: Get mongos start command of the nodes from CSDB

         start_mongod_services_using_script: Start mongod services using a script

         disable_authentication_mongos: Disable authentication on
         mongos server for restore validation

         start_mongos_server: Start mongos server

         getMongosList: Returns list of mongos nodes in a sharded cluster

         initiates_replicaset_or_shard: Initiate sharded cluster/replica set

         validateRestore: Validate restore

         startMongosServiceUsingScript: Start Mongos node as a service using script

         delete_test_data: Deletes databases that start with given prefix

         check_if_single_node_replicaset_from_DB: Check in CS DB is the server type for the instance is 4
         which implies single node replica set

         check_if_sharded_cluster: Check if the instance is a sharded cluster

         check_if_replica_set: Check if the instance is a replica set

         check_single_node_replica_set: connect to cluster and check if it
         is a single node replica set
         
        db_object: Return the mongo database object
         
        collection_object: Return the collection object
        
        create_document: Create a document in the collection
        
        get_document: Get a document from the collection
        
        update_document: Update a document in the collection
        
        delete_document: Delete a document from the collection


    MongoAgentHelper (class) which performs Mongo Agent related Operations.

         __int__ :Constructor for MongoAgentHelper class,
          which creates connection to the replica set/sharded cluster

          populate_tc_inputs : populates user input to perform operations

           add_instance()   --  add new instance for Mongo DB instance

          add_mongodb_pseudo_client: to add mongoDB pseudo client to commcell.

          discover_mongodb_nodes: Discover running nodes and state of MOngoDB running

          run_mongodb_snap_backup: RUn snap backup of MOngo Agent.
                                    (As we have spool copy we run backupcopy inline)


          run_mongodb_inplace_restore: inplace restore of Mongo instance.

          validate_bigdata_app_list: validates if client is part of bigdata apps agent.

          get_client_jobs: Get clients jobs for provided client

          get_logs_for_job_from_file: Get logs on particular job id and machine.

          verify_cluster_restore: Verify contents of cluster restore.


"""

import string
import random
import datetime
import time
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from cvpysdk.agent import Agent
from cvpysdk.client import Clients
from cvpysdk.backupset import Backupset
from cvpysdk.subclient import Subclient
from Server.JobManager.jobmanager_helper import JobManager
import pymongo
import certifi


class MongoDBHelper:
    """Class which establishes connection with replica-
    set/sharded cluster and performs DB operations.

    """

    def __init__(self, commcell, masterhostname, port=27017, db_user='',
                 db_password='', replset=None, auth_database='admin',
                 bin_path='/usr/bin', connectionstring='', atlas=0):
        """ Initialize MongoDBhelper object.

        Args:
            commcell                    (obj) -- Commcell object
            masterhostname              (str) -- master node hostname
            port                        (int) -- master node port number
            db_user                      (str) -- DB username
                        default:' '
            db_password                  (str) -- DB password
                        default:' '
            replset                     (str) -- replica set name if not sharded cluster
                        default:None
            auth_database                (str) -- authentication database
                        default:admin
            bin_path                    (str) -- bin path of MongoDB binaries
                        default:'/usr/bin'
            atlas                       (int) -- 0 - if it is not an Atlas cluster
                                                 1 - if it is an Atlas cluster
        Return:
            object - instance of this class

        """
        if atlas == 1:
            self.connection_string = connectionstring
            self.access_node = masterhostname
            self.atlas = 1
        else:

            self.atlas = 0
            self.csdb = database_helper.CommServDatabase(commcell)
            self.host_name = masterhostname
            self.user = db_user
            self.password = db_password
            self.port = port
            self.database_name = auth_database
            self.repset = replset
            self.bin_path = bin_path
            self.connection_string = f'mongodb://mongoadmincv:{self.password}@{self.host_name}:27017/?authMechanism=DEFAULT'
        self.commcell = commcell
        self.log = logger.get_log()
        self._connection = None
        self._connect()
        self.log.info("Initialised MongoDB helper object")
        self.use_script = 0
        self._mongodb_association_details = None

    def __enter__(self):
        """Return the current instance.

                    Returns:
                        object - the initialized instance referred by self

        """
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Close database connection if exists before exit."""
        if self._connection:
            self._connection.close()
            self.log.info("Closing connection")
            self._connection = None

    def __del__(self):
        """Destructor"""
        del self

    def close_connection(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self.log.info("closing connection")
            self._connection = None

    @property
    def connection(self):
        """ Return the connection object established with the master node of the replica set."""
        return self._connection

    def _connect(self):
        """Establish connection with the master node of the replica set or sharded cluster."""
        try:
            if self.atlas == 1:
                connection = pymongo.MongoClient(self.connection_string, tlsCAFile=certifi.where()) or None
            else:
                connection = pymongo.MongoClient(
                    self.host_name,
                    port=self.port,
                    username=self.user,
                    password=self.password,
                    authSource=self.database_name,
                    replicaSet=self.repset
                ) or None
            self.log.info("Connection established")
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception('Exception: {0}'.format(str(exception_case)))
        except Exception as excp:
            raise Exception(
                'Failed to connect to the MongoDB Server\nError: "{0}"'.format(excp))
        if connection is not None:
            self._connection = connection

    def __create_db(self, database):
        """ Create a MongoDB database in the primary node/ mongos node.

        Args:
            database             (str) -- database name
        Returns:
            db_obj                database object

        """
        try:
            if self.__check_if_db_exists(database):
                self.__drop_db(
                    database)
            db_obj = self._connection[database]
            self.log.info("Created database :%s", database)
            return db_obj
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception('Exception: {0}'.format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Unable to create db:{0}".format(str(exception_case)))

    def __drop_db(self, database):
        """Drop the database from the primary node/mongos node.

        Args:
            database              (str) -- database name

        """
        try:
            self._connection.drop_database(database)
            self.log.info("Dropped database: %s", database)
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception('Exception: {0}'.format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Unable to drop db: {0}".format(str(exception_case)))

    def __check_if_db_exists(self, database):
        """ Check if the database exists in the primary node/mongos node.

        Args:
            database             (str) -- database name
        Returns:
            Boolean                    -- True if database exists else false

        """
        try:
            db_list = self.get_db_list() or None
            self.log.info("Checking if database  %s exists in the server", database)
            if database not in db_list and db_list is not None:
                return False
            return True
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception('Exception: {0}'.format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Unable to check the db existance"
                            ": {0}".format(str(exception_case)))

    def get_db_list(self):
        """Return a list of database from the primary node of
           the replica set/mongos server of a sharded cluster.

           Returns:
                db_list (list) -- list of databases

        """
        try:
            self.log.info("Fetching the list of database in the server")
            db_list = self._connection.list_database_names()
            return db_list
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception('Exception: {0}'.format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Unable to get list:{0}".format(str(exception_case)))

    def __create_collection(self, db_obj, col_name):
        """Create a collection with specific name in primary node of
        the replica set/mongos server of a sharded cluster.

        Args:
            db_obj                 -- database object
            col_name         (str) -- collection_name
        Returns:
            col_obj                -- collection object

        """
        try:
            col_obj = db_obj[col_name]
            self.log.info("Created a collection with name %s", col_name)
            return col_obj
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception('Exception: {0}'.format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Unable to create collection:{0}".format(str(exception_case)))

    def drop_collections(self, db_name, col_names):
        """
        Method to drop a collections under a database

            Args:
                db_name (str) -- Name of the db
                col_name (List) -- List of names of collection
        """
        try:
            for col_name in col_names:
                self._connection[db_name].drop_collection(col_name)
            self.log.info("dropped collections with name %s",col_names)
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception('Exception: {0}'.format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Unable to drop db: {0}".format(str(exception_case)))

    @staticmethod
    def id_generator(size=25, chars=string.ascii_uppercase + string.digits):
        """Generate random characters for document content.

        Returns:
            value             (str) -- value generated

        """
        value = str(''.join(random.choice(chars) for _ in range(size)))
        return value

    def db_object(self, db_name: str) -> object:
        """Return the mongo database object.

        Args:
            db_name (str)  --   database name
            
        Returns:
            db_obj  (obj)  --   database object

        """
        try:
            db_obj = self._connection[db_name]
            return db_obj
        except Exception as error:
            raise Exception(f"Unable to get database object: {str(error)}")
        
    def collection_object(self, db_name: str, col_name: str) -> object:
        """Return the collection object.

        Args:
            db_name (str)  --   database name
            col_name (str) --   collection name
            
        Returns:
            col_obj (obj)  --   collection object

        """
        try:
            col_obj = self._connection[db_name][col_name]
            return col_obj
        except Exception as error:
            raise Exception(f"Unable to get collection object: {str(error)}")

    def create_document(self, col_obj):
        """Create a document in primary node of the replica set/mongos
         server of a sharded cluster.

        Args:
            col_obj                 -- collection object

        """
        try:
            mydict = {
                "name": "{0}_{1}_{2}".format(str(MongoDBHelper.id_generator),
                                             str(MongoDBHelper.id_generator),
                                             str(MongoDBHelper.id_generator)),
                'rating': random.randint(1, 5),
                'timeNow': datetime.datetime.now()
            }
            col_obj.insert_one(mydict)
            self.log.info("Inserted document")
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception('exception: {0}'.format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Unable to create document:{0}".format(str(exception_case)))

    def get_document(self, col_obj: object, query: str) -> dict:
        """ Get a document from the collection

        Args:
            col_obj (obj)  --   collection object
            query   (str)  --   query to get the document

            Example:
                query = {"name": "test"}

        Returns:
            document (dict)  --   document fetched from the collection

        """
        try:
            self.log.info(f"Fetching document with query: {query}")
            document = col_obj.find_one(query)
            self.log.info("Successfully fetched document")
            return document
        except Exception as error:
            raise Exception(f"Unable to get document: {str(error)}")

    def update_document(self, col_obj: object, query: str, new_values: dict) -> None:
        """ Update a document in the collection.

        Args:
            col_obj (obj)       --   collection object
            query   (str)       --   query to update the document
            new_values (dict)   --   new values to update the document

            Example:
                query = {"name": "test"}
                new_values = {"$set": {"name": "test1"}}
        """
        try:
            col_obj.update_one(query, new_values)
            self.log.info("Updated document")
        except Exception as error:
            raise Exception(f"Unable to update document: {str(error)}")

    def delete_document(self, col_obj: object, query: str) -> None:
        """Method to delete a document from the collection.

        Args:
            col_obj (obj)       --   collection object
            query   (str)       --   query to delete the document
            
            Example:
                query = {"name": "test"}
        """
        try:
            col_obj.delete_one(query)
            self.log.info("Successfully deleted document!")
        except Exception as error:
            raise Exception(f"Unable to delete document: {str(error)}")

    def __count_documents_in_collection(self, col_obj):
        """Count the number of documents in the collection for validation.

        Args:
            col_obj                        -- collection object
        Returns:
                (int)                      -- number of documents in collection

        """
        try:
            self.log.info("Counting number of documents in the collection ")
            return col_obj.count_documents({})
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception('exception: {0}'.format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Unable to count documents:{0}".format(str(exception_case)))

    def get_collection_list(self, database):
        """Return a list of collection in the database.

         Args:
             database                     (str)  -- database name
         Returns:
                                          (list) -- collections in database

         """
        try:
            self.log.info("Fetching the list of collections in the database %s ", database)
            return self._connection[database].list_collection_names()
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception('exception: {0}'.format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Unable to get collections:{0}".format(str(exception_case)))

    def generate_test_data(self, database_prefix="auto_db", num_dbs=4, num_col=5, num_docs=5):
        """Generate test data in the primary node of replica set/mongos of the sharded cluster.

        Args:
            database_prefix                 (str)  --  database name
            num_dbs                         (int)  --  number of dbs
            num_col                         (int)  --  number of collection
            num_docs                        (int)  --  number of documents
        Returns:
            datalist                        (list) --  inserted data

        """
        try:
            collection_prefix = "auto_collection"
            datalist = {}
            for each_db in range(0, num_dbs):
                dbname = database_prefix + str(int(time.time())) + str(each_db)
                db_obj = self.__create_db(dbname)
                datalist[dbname] = []
                for each_col in range(0, num_col):
                    colname = collection_prefix + str(int(time.time())) + str(each_col)
                    col_obj = self.__create_collection(db_obj, colname)
                    datalist[dbname].append(colname)
                    if each_col == (num_col - 1):
                        datalist[dbname].append(num_docs)
                    for _ in range(0, num_docs):
                        self.create_document(col_obj)
            self.log.info(datalist)
            self.log.info("Test data generated")
            return datalist
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception('exception: {0}'.format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Unable populate data:{0}".format(str(exception_case)))

    def shutdown_mongodb_server(self, clientname, port=27017, user='', passwd=''):
        """Shuts down the MongoDB server which has authentication enabled.

        Args:
            clientname               (str)  --  client name
            port                     (int)  --  port number
            user                     (str)  --  DB user
            passwd                   (str)  --  DB password
        Raises:
            Exception:
                     If shutdown is successful

        """
        try:
            self.log.info("Shutting down mongodb server")
            if not clientname.strip():
                clientname = self.host_name
            if not user.strip():
                user = self.user
            if not passwd.strip():
                passwd = self.password
            cl_machine = self.commcell.clients.get(clientname)
            hostname = str(cl_machine.client_hostname)
            client_connection = pymongo.MongoClient(hostname, port=port, username=user,
                                                    password=passwd, authSource="admin")
            db = client_connection["admin"]
            result = db.eval(db.command({'shutdown': 1, 'force': 'true'}))
            self.log.info("Failed to shutdown the server: %s", str(result))
        except pymongo.errors.AutoReconnect as exception_case:
            self.log.info("shutdown_mongodb_server suceeded")
            self.log.info("Exception:%s", str(exception_case))
            self.log.info("Clientname:" + clientname + ",port:" + port)
            pass
        except Exception as exception_case:
            # raise Exception("unable to shutdown server ",result)
            self.log.info("shutdown_mongodb_server suceeded")
            self.log.info("Exception: %s", str(exception_case))
            self.log.info("Clientname:" + clientname + ",port:" + port)
            pass

    def check_shardedcluster_or_replicaset(self, pseudoclient):
        """Check if the Mongod server is a replica set or sharded cluster.

        Args:
            pseudoclient                  (str) -- pseudoclient name
        Returns:
            result                        (int) -- 1 if sharded cluster, 0 if replica set

        """
        try:
            self.log.info("Checking if the server is a replica set or sharded cluster")
            pclient = self.commcell.clients.get(pseudoclient)
            agent = pclient.agents.get('big data apps')
            instancelist = agent.instances.all_instances
            instanceid = instancelist[pclient.client_name]
            query = "select CASE WHEN EXISTS(select 1 from APP_MongoDbAssociation" \
                    " where instanceId={0} AND subType =3)" \
                    "THEN 1 ELSE 0 END ".format(instanceid)
            self.csdb.execute(query)
            self.log.info("%s executed", query)
            result = self.csdb.fetch_one_row()
            result = int(result[0])
            self.log.info("result: %s", str(result))
            return result
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception("Exception: {0}".format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("unable to identify sharded cluster or "
                            "replica set:{0}".format(str(exception_case)))

    def get_db_server_size(self):
        """Return MongoDB server size.

        Returns:
            totalsize              --  size of the server

        """
        try:
            self.log.info("Fetching database server size")
            totalsize = 0
            if not self._connection:
                newcon = pymongo.MongoClient(self.host_name, port=self.port,
                                             username=self.user, password=self.password,
                                             authSource="admin", repset=self.repset)
            else:
                newcon = self._connection
            db = newcon["admin"]
            databaselist = db.command("listDatabases")
            dblist = databaselist["databases"]
            for database in dblist:
                if not database["name"] in ("admin", "config", "local"):
                    totalsize += int(database["sizeOnDisk"])
            self.log.info("Total size: %s", str(totalsize))
            return totalsize
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception("Exception: {0}".format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("unable to identify sharded cluster or replica "
                            "set size:{0}".format(str(exception_case)))

    def shutdown_server_using_kill_command(self):
        """Shutdown server using kill command when authentication is not enabled.

        """
        self.log.info("Shutting down server using kill command "
                      "since authentication is not enabled post restore")
        result = self._mongodb_association_details
        clntlist = []
        for each_row in result:
            clntlist.append(str(each_row[1]))
        client_list = set(clntlist)
        client_list = list(map(str, client_list))
        self.close_connection()
        self.log.info(client_list)
        for clnt in client_list:
            try:
                cl_machine = Machine(clnt, self.commcell)
                self.log.info(cl_machine)
                if "unix" in str(cl_machine.os_info.lower()):
                    self.log.info("command:'killall -2 mongod;killall -2 mongos'")
                    exitcode, output, error = cl_machine.execute_command("killall -2 mongod"
                                                                         ";killall -2 mongos")
                    self.log.info("exitcode: %s,output: %s,"
                                  "error: %s", str(exitcode), output, error)
                else:
                    exitcode, output, error = cl_machine.execute_command("taskkill"
                                                                         " /f /im mongos.exe")
                    self.log.info(
                        "command:'taskkill /f /im mongod.exe',exitcode: %s,output: %s,"
                        "error: %s", str(exitcode), output, error)
            except pymongo.errors.AutoReconnect as exception_case:
                self.log.info("Exception: %s", str(exception_case))
                pass
            except Exception as exception_case:
                self.log.info("Exception: %s", str(exception_case))
                pass

    def get_replicaset_or_shardedcluster(self, discover_nodes_table):
        """Identify if replica set or Sharded cluster from discover nodes table.

        Args:
            discover_nodes_table               (table) --  discovered nodes table
        Returns:
            (int)                                      --  0 if replica set, 1 for sharded cluster

        """
        replica_or_shard = discover_nodes_table.get_column_data('Server type')[0]
        self.log.info("Identify replica set or shard from the discovery table")
        if replica_or_shard == 'REPLICA_SET':
            return 0
        return 1

    def __check_for_service(self):
        """Check MongoDB server information."""
        try:
            self.log.info("Check for MongoDB server status")
            self.log.info("Server information: %s", str(self._connection.server_info()))
            return 0
        except Exception as exception_case:
            self.log.info("Failed to get MongoDB server status information")
            self.log.info("Exception: %s", str(exception_case))
            return 1

    def __get_mongodbassociationdetails_from_csdb(self, pseudoclient):
        """Get MongoDB cluster /replica set details from CS DB.

        Args:
            pseudoclient                     (str) --  pseudoclient name
        Returns:
            result                                 -- MongoDB association SQL query result

        """
        try:
            self.log.info("Fetching details from app_MongoDbAssociation table")
            self.commcell.clients.refresh()
            cl_machine = self.commcell.clients.get(self.host_name)
            clientid = cl_machine.client_id
            pclient = self.commcell.clients.get(pseudoclient)
            agent = pclient.agents.get('big data apps')
            instancelist = agent.instances.all_instances
            instanceid = instancelist[pclient.client_name]
            query = "select id,hostname,portnumber,subtype,dataPath,cmdLineOption,repsetname," \
                    "confgfilepath from APP_MongoDbAssociation where instanceId={0}" \
                    " and modified=0 order by subtype desc,id" \
                    " desc".format(instanceid)
            self.log.info("'%s' to be executed", query)
            self.csdb.execute(query)
            result = self.csdb.fetch_all_rows()
            self.log.info("result: %s", str(result))
            if result and self.use_script == 0:
                for row in result:
                    if row[7] and ' ' in row[7]:
                        self.use_script = 1
                        break
            self._mongodb_association_details = result
            return result
        except Exception as exception_case:
            self.log.info("Failed to get MongoDB association "
                          "details from CS DB. Exception: %s", str(exception_case))

    def shutdown_server_and_cleanup_using_command(self, user='',
                                                  passwd='', only_shutdown=0):
        """Shutdown mongodb server and cleanup dbpath with onlyShutdown is set to 0.

        Args:
            user                              (str)  --  DB user
            passwd                            (str)  --  DB password
            only_shutdown                     (int)  --  0 if shutdown and cleanup,
                                                         1 if only shutdown
        Raises:
            Exception:
                       If shutdown is successful and continues with cleanup of dbpath

        """
        self.log.info("Shutdown MongoDB server and cleanup the dbapth")
        if not user.strip():
            user = self.user
        if not passwd.strip():
            passwd = self.password
        flag = 1
        cmd = ''
        cmd1 = ''
        cmd2 = ''
        result = self._mongodb_association_details
        for each_row in result:
            try:
                cl_machine = self.commcell.clients.get(each_row[1])
                if "unix" in str(cl_machine.os_info.lower()):
                    newcon = pymongo.MongoClient(each_row[1], port=int(each_row[2]),
                                                 username=user, password=passwd,
                                                 authSource="admin") or None
                    db = newcon["admin"]
                    dbpath = str(each_row[4])
                    if int(each_row[3]) != 3 and dbpath.strip():
                        cmd = "rm -rf " + dbpath.strip() + "/*"
                        flag = 0
                    db.eval(db.command({'shutdown': 1, 'force': 'true'}))
                else:
                    newcon = pymongo.MongoClient(each_row[1], port=int(each_row[2]),
                                                 username=user, password=passwd,
                                                 authSource="admin")
                    db = newcon["admin"]
                    dbpathname = str(each_row[4])
                    if int(each_row[3]) != 3 and dbpathname.strip():
                        cmd1 = 'forfiles /P "' + dbpathname + \
                               '" /M * /C "cmd /c if @isdir==FALSE del @file"'
                        cmd2 = 'forfiles /P "' + dbpathname + \
                               '" /M * /C "cmd /c if @isdir==TRUE rmdir /S /Q @file"'
                        flag = 0
                    db.eval(db.command({'shutdown': 1, 'force': 'true'}))
            except Exception as exception_case:
                cl_machine = self.commcell.clients.get(each_row[1])
                if "unix" in cl_machine.os_info.lower() and flag == 0 and only_shutdown == 0:
                    exitcode, output, error = cl_machine.execute_command(cmd)
                    self.log.info("command: '%s',exitcode : %s, output: %s, error: %s, "
                                  "exception: %s", cmd, str(exitcode), output,
                                  error, str(exception_case))
                    flag = 1
                    if exitcode == 0:
                        self.log.info("dbpath was cleaned successfully")
                elif "windows" in cl_machine.os_info.lower() and flag == 0 and only_shutdown == 0:
                    exitcode1, output, error = cl_machine.execute_command(cmd1)
                    self.log.info("command: '%s',exitcode : %s, output: %s, error: %s, "
                                  "exception: %s", cmd1, str(exitcode1), output,
                                  error, str(exception_case))
                    self.log.info("Exception e: %s", exception_case)
                    exitcode2, output, error = cl_machine.execute_command(cmd2)
                    self.log.info("command: '%s',exitcode : %s, output: %s, error: %s, "
                                  "exception: %s", cmd2, str(exitcode2), output,
                                  error, str(exception_case))
                    self.log.info("Exception e: %s", str(exception_case))
                    flag = 1
                    if exitcode1 == 0 and exitcode2 == 0:
                        self.log.info("dbpath was cleaned successfully")
                        self.log.info(str(exception_case))
                elif flag == 0 and only_shutdown == 1:
                    self.log.info("onlyShutdown completed")
                    self.log.info(str(exception_case))
                    flag = 1
                else:
                    self.log.info("It is a Mongos Server")
                    self.log.info("Exception: %s", str(exception_case))
                pass

    def validate_discovery_of_nodes(self, pseudoclient, port_list, client_list, subtype_list):
        """Validate discovery of nodes.

        Args:
            pseudoclient                 (str)  -- pseudoclient name
            port_list                     (list) -- list of ports from discovered table
            client_list                   (list) -- list of clients from discovered table
            subtype_list                  (list) -- list of server type from discovered table
        Returns:
                                          (boolean) -- true, if discovery is successful,
                                                       else false

        """
        try:
            self.log.info("Validate discovery of nodes")
            for node, i in enumerate(subtype_list):
                if i.lower() == "replica_set":
                    subtype_list[node] = 2
                elif i.lower() == "config_server":
                    subtype_list[node] = 4
                else:
                    subtype_list[node] = 3
            result = self.__get_mongodbassociationdetails_from_csdb(pseudoclient)
            if len(result) == len(port_list):
                flag = 0
                for client, port, subtype in zip(client_list, port_list, subtype_list):
                    clhostname = self.commcell.clients.get(client)
                    clhostname = clhostname.client_hostname
                    for row in result:
                        if row[1] == clhostname and int(row[2]) == int(port) \
                                and int(row[3]) == int(subtype):
                            flag = 1
                            break
                    if flag == 0:
                        return False
                    flag = 0
            self.log.info("Discovery validation successful")
            return True
        except pymongo.errors.AutoReconnect as exception_case:
            self.log.info("Exception: %s", str(exception_case))
            return False
        except Exception as exception_case:
            self.log.info("Exception: %s", str(exception_case))
            return False

    def get_mongod_start_command_from_csdb(self):
        """Get MongoDB server start command from CS DB.

        Returns:
            mongod_start_server_list        (list)--  list of mongod server start commands

        """
        mongod_start_server_list = {}
        try:
            self.log.info("Fetching Mongod start command form CS DB")
            result = self._mongodb_association_details
            for row in result:
                if int(row[3]) != 3:
                    if row[1] not in mongod_start_server_list.keys():
                        mongod_start_server_list[row[1]] = [row[5] + "::" + str(row[2])]
                    else:
                        mongod_start_server_list[row[1]].append(row[5] + "::" + str(row[2]))
        except Exception as exception_case:
            self.log.info("Failed to fetch mongod server start commands")
            self.log.info("Exception: %s", str(exception_case))
            pass
        self.log.info("Start server list:")
        self.log.info(mongod_start_server_list)
        return mongod_start_server_list

    def get_mongos_start_command_from_csdb(self):
        """Get mongos server start command from CS DB.

        Returns:
            cmd                             (list)--  mongos server start command

        """
        cmd = ""
        try:
            self.log.info("Get mongos start command from CS db")
            result = self._mongodb_association_details
            for row in result:
                if int(row[3]) == 3 and self.host_name == row[1] and self.port == int(row[2]):
                    cmd = row[5]
        except Exception as exception_case:
            self.log.info("Failed to fetch mongod server start commands ")
            self.log.info("Exception: %s", str(exception_case))
            pass
        return cmd

    def start_mongod_services(self, startcmdlist):
        """Start mongod service.

        Args:
            startcmdlist          (list) -- list of clients and commands to start the mongod server

        """
        self.log.info("Start mongod services on the client")
        if ' ' in self.bin_path or self.use_script == 1 or '\\' in self.bin_path:
            self.start_mongod_services_using_script(startcmdlist)
            return
        mongodclients = startcmdlist.keys()
        mongodstartcmds = startcmdlist.values()
        for mclient, mscmdlist in zip(mongodclients, mongodstartcmds):
            try:
                client = self.commcell.clients.get(mclient)
                for mscmd in mscmdlist:
                    mstart = mscmd.split("::")
                    mscmd = mstart[0]
                    exitcode, output, error = client.execute_command(
                        mscmd, wait_for_completion=True)
                    self.log.info("start mongod outputs: exitcode:%s,output:%s,"
                                  "error: %s", str(exitcode), output, error)
                    if exitcode == 0:
                        self.log.info("successfully started mongod server on %s using "
                                      "start command %s", str(mclient), mscmd)
                    elif exitcode == 48:
                        self.log.info("Service is already running on %s"
                                      " using start command %s", str(mclient), mscmd)
                    else:
                        self.log.info("Failed to start mongod server on %s using "
                                      "start command %s", str(mclient), mscmd)
                        self.log.info("start mongod outputs: exitcode:%s,output:%s,"
                                      "error: %s", str(exitcode), output, error)
            except pymongo.errors.AutoReconnect as exception_case:
                self.log.info("Manually start the Server.")
                self.log.info(str(exception_case))
                pass
            except Exception as exception_case:
                self.log.info("Manually start the Server. Exception"
                              ": %s", str(exception_case))
                pass

    def start_mongod_services_using_script(self, startcmdlist):
        """Start Mongod server as a script.

        Args:
            startcmdlist        (list) -- list of clients and commands to start the mongod server

        """
        self.log.info("Start mongod service as a script")
        mongodclients = startcmdlist.keys()
        mongodstartcmds = startcmdlist.values()
        for mclient, mscmdlist in zip(mongodclients, mongodstartcmds):
            try:
                client = self.commcell.clients.get(mclient)
                client_obj = Machine(client)
                controller_obj = Machine()
                for mscmd in mscmdlist:
                    mstart = mscmd.split("::")
                    mscmd = mstart[0]
                    prt = str(mstart[1])
                    if client_obj.os_info == 'UNIX':
                        config_file = "startserver.sh"
                        if not controller_obj.check_directory_exists(constants.TEMP_DIR):
                            controller_obj.create_directory(constants.TEMP_DIR)
                        local_config_path = controller_obj.join_path(constants.TEMP_DIR,
                                                                     config_file)
                        remote_path = client_obj.join_path(client.install_directory, "Base")
                        remote_path = client_obj.join_path(remote_path, "TempConfig")
                        if not client_obj.check_directory_exists(remote_path):
                            client_obj.create_directory(remote_path)
                        file_path = open(local_config_path, 'w', newline='\n')
                        if mscmd is not None:
                            file_path.write(mscmd)
                            self.log.info("Start command: %s", str(mscmd))
                    else:
                        config_file = "startserver.bat"
                        if not controller_obj.check_directory_exists(constants.TEMP_DIR):
                            controller_obj.create_directory(constants.TEMP_DIR)
                        local_config_path = controller_obj.join_path(constants.TEMP_DIR,
                                                                     config_file)
                        # remote_path = clientObj.join_path(client.install_directory, "Base")
                        remote_path = "C:"
                        remote_path = client_obj.join_path(remote_path, "TempConfig")
                        if not client_obj.check_directory_exists(remote_path):
                            client_obj.create_directory(remote_path)
                        file_path = open(local_config_path, 'w')
                        if mscmd is not None:
                            service_name = "mongod_{0}_automation".format(str(prt))
                            cmd_to_delete = "sc delete {0}".format(service_name)
                            cmd_to_create = "{0} --install --serviceName {1} " \
                                            "--serviceDisplayName {2}" \
                                            "".format(mscmd, service_name,
                                                      "mongod_{0}_automation".format(str(prt)))

                            cmd_to_start = "net start {0}".format(service_name)
                            file_path.write(cmd_to_delete + "\n" + cmd_to_create + "\n"
                                            + cmd_to_start)
                            self.log.info("File contents: %s , %s , %s"
                                          "", cmd_to_delete, cmd_to_create, cmd_to_start)
                    file_path.close()
                    copy_status = client_obj.copy_from_local(local_config_path, remote_path)
                    self.log.info("copy_status :%s", copy_status)
                    if copy_status is False:
                        raise Exception("Failed to copy file to "
                                        "remote machine.Exiting")
                    if client_obj.os_info == 'UNIX':
                        remote_config_file = client_obj.join_path(remote_path, "startserver.sh")
                        exitcode, output, error = client.execute_script(script_type="UnixShell",
                                                                        script=remote_config_file,
                                                                        wait_for_completion=True)
                        self.log.info("start mongod outputs: exitcode:%s,output:%s,"
                                      "error: %s", str(exitcode), output, error)
                    else:
                        remote_config_file = client_obj.join_path(remote_path, "startserver.bat")
                        exitcode, output, error = client.execute_script(script_type="WindowsBatch",
                                                                        script=remote_config_file,
                                                                        wait_for_completion=True)
                        self.log.info("start mongod outputs: exitcode:%s,output:%s,"
                                      "error: %s", str(exitcode), output, error)
                    if exitcode == 0:
                        self.log.info("successfully started mongod server on %s using start "
                                      "command %s", str(mclient), str(mscmd))
                    elif exitcode == 48:
                        self.log.info("Service is already running "
                                      "on %s using start command %s", str(mclient), str(mscmd))
                    else:
                        self.log.info("Failed to start mongod server on %s using start "
                                      "command %s", str(mclient), str(mscmd))
                        self.log.info("start mongod outputs: exitcode: %s,output: %s,"
                                      "error: %s", str(exitcode), output, error)
                    controller_obj.delete_file(local_config_path)
                    client_obj.delete_file(remote_config_file)
            except pymongo.errors.AutoReconnect as exception_case:
                self.log.info("Exception: %s", str(exception_case))
                pass
            except Exception as exception_case:
                self.log.info("Exception: %s", str(exception_case))
                pass

    def disable_authentication_mongos(self, startcmd):
        """Disable authentication in Mongos server for restore
         validation and return new start command.

        Args:
            startcmd                           (str) --  start command for mongos server
        Returns:
            new_start_cmd                        (str) --  start command with
                                                           authentication disabled

        """
        try:
            idx = 0
            configfile = ''
            new_start_cmd = startcmd.replace("--auth", " ")
            new_start_cmd = ' '.join(new_start_cmd.split())
            new_start_cmd = new_start_cmd.split()
            if "--keyfile" in new_start_cmd:
                idx = new_start_cmd.index('--keyfile')
                idx += 1
                del new_start_cmd[idx]
                del new_start_cmd[idx - 1]
            if "--auth" in new_start_cmd:
                idx = new_start_cmd.index('--auth')
                del new_start_cmd[idx]
            if "-f" in new_start_cmd:
                idx = new_start_cmd.index('-f')
                idx += 1
                configfile = new_start_cmd[idx]
            if "--config" in new_start_cmd:
                idx = new_start_cmd.index('--config')
                idx += 1
                configfile = new_start_cmd[idx]
            if configfile.strip():
                client_machine_obj = self.commcell.clients.get(self.host_name)
                if "unix" in client_machine_obj.os_info.lower():
                    cmd = 'grep -viE "(security:|keyfile:|' \
                          'auth)" {0} > {1}'.format(configfile, configfile + "tmp")
                    exitcode, output, error = client_machine_obj.execute_command(cmd)
                    self.log.info("command: %s, exitcode: %s,output: %s,"
                                  "error: %s", cmd, str(exitcode), output, error)
                    if exitcode != 0:
                        self.log.info("copy failed")
                        return 1
                    new_start_cmd[idx] = new_start_cmd[idx].strip('"')
                    new_start_cmd[idx] = '"' + configfile + "tmp" + '"'
                    self.log.info("Start command: %s", ' '.join(new_start_cmd))
                elif "windows" in client_machine_obj.os_info.lower():
                    cmd = 'for %F in ({}); do findstr /v "authorization' \
                          ' keyfile: security:"  %F >' \
                          ' {} '.format(configfile, configfile + "tmp")
                    exitcode, output, error = client_machine_obj.execute_command(cmd)
                    self.log.info("command: %s, exitcode: %s,output: %s,"
                                  "error: %s", cmd, str(exitcode), output, error)
                    if exitcode != 0:
                        self.log.info("copy failed")
                        return 1
                    new_start_cmd[idx] = new_start_cmd[idx].strip('"')
                    new_start_cmd[idx] = configfile + "tmp"
                    self.log.info("Start command: %s", ' '.join(new_start_cmd))
                else:
                    self.log.info("os information is not identified")
            return ' '.join(new_start_cmd)
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception("Exception: {0}".format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Unable disable authentication:"
                            "{0}".format(str(exception_case)))

    def start_mongos_server(self, startcmd="mongos"):
        """Start Mongos server.

        Args:
            startcmd                     (str) -- commands to start the mongos server

        """
        try:
            if ' ' in self.bin_path or self.use_script == 1 or '\\' in self.bin_path:
                self.start_mongos_service_using_script(startcmd)
                return
            self.log.info("Starting mongos server")
            client = self.commcell.clients.get(self.host_name)
            exitcode, output, error = client.execute_command(startcmd, wait_for_completion=True)
            self.log.info("command: %s, exitcode: %s,output: %s,"
                          "error: %s", startcmd, str(exitcode), output, error)
            self.log.info("Start mongos output: exitcode: %s,output: %s,"
                          "error: %s", str(exitcode), output, error)
            if exitcode == 0:
                self.log.info("successfully started mongos server")
            elif exitcode == 48:
                self.log.info("Service is already running")
            else:
                self.log.info("Failed to start mongos server")
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception("Exception: {0}".format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Unable start mognos server:{0}".format(str(exception_case)))

    def get_mongos_list(self, node_table, client_list, port_list):
        """Get mongos server list.

        Args:
            node_table                   (table) --  discovered nodes table
            client_list                  (list)  --  list of clients
            port_list                    (list)  --  list of ports
        Returns:
            mongoslist                  (list)  --  list of mongos servers

        """
        try:
            self.log.info("Get mongos list")
            mongoslist = {}
            subtype_list = node_table.get_column_data('Subtype')
            for node, i in enumerate(subtype_list):
                if "mongos" in i.lower():
                    mongoslist[client_list[node]] = port_list[node]
            self.log.info("mongos list:")
            self.log.info(mongoslist)
            return mongoslist
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception("Failed to get mongos list:{0}".format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Failed to get mongos list:{0}".format(str(exception_case)))

    def initiate_replicaset_or_shard(self, restorenodelist, replicasetlist):
        """Initiate a replica set/sharded cluster.

        Args:
            restorenodelist        (dict)  -- {replicasetname: hostname_port}
            replicasetlist         (dict)  -- {replicasetname: [hostname1_port1,hostname2_port2...]}

        """
        try:
            self.log.info("Initiate a replica set or sharded cluster")
            for restorenode_rs_name, restorehost_port in restorenodelist.items():
                restorehost, restoreport = restorehost_port.split('_')
                replicasethost_port_list = replicasetlist[restorenode_rs_name]
                db_connection = pymongo.MongoClient(restorehost, port=int(restoreport),
                                                    username=self.user, password=self.password,
                                                    authSource="admin")
                db = db_connection['admin']
                config = db.command({'replSetGetConfig': 1})
                self.log.info("config: %s", str(config))
                # mlist = ''
                mid = 0
                for replicasethostport in replicasethost_port_list:
                    host, port = replicasethostport.split('_')

                    if host == restorehost and int(port) == int(restoreport):
                        continue
                    replicasethostport = replicasethostport.replace("_", ":")
                    mid += 1
                    # mlist=mlist+"{'_id':"+str(mid)+",'host':'"+str(replicasethostport)+"'},"
                    config['config']['members'].append({'_id': int(mid),
                                                        'host': str(replicasethostport)})
                # mlist=mlist[:-1]
                # config['config']['members'].append(mlist)
                config['config']['version'] += 1
                self.log.info("Post updation config: %s", str(config))
                result = db.command({'replSetReconfig': config['config']})
                self.log.info("result: %s", str(result))
                # mlist = ''
        except pymongo.errors.AutoReconnect as exception_case:
            self.log.info("Failed to initiate replica set. Please do it manually.")
            self.log.info("Exception:%s", str(exception_case))
            pass
        except Exception as exception_case:
            self.log.info("Faied to initiate replica set. Please do it manually")
            self.log.info("Exception: %s", str(exception_case))
            pass

    def get_data_hash(self, datalist, db_connection=None):
        """Returns db hash for the given datalsit
        Args:
            datalist        (list)      --  data to be validated
            db_connection   (obj)       --  connection object
        Returns:
            dbhash_list     (dict)      --  hash of databases
        """
        dbhash_list = {}
        if db_connection is None:
            db_connection = self._connection
        for database in datalist:
            db_obj = db_connection[database]
            db_hash_temp = db_obj.command({'dbHash': 1})
            hash_keys = ['collections', 'md5']
            db_hash = {key: db_hash_temp[key] for key in hash_keys}
            if database.endswith('_restore'):
                database = database.replace('_restore', '')
            elif datalist[database][0].endswith('_restore'):
                db_hash['collections'] = {coll.replace('_restore', ''): db_hash['collections'][coll]
                                          for coll in datalist[database]}
                db_hash['md5'] = None
            dbhash_list.update({database: db_hash})
        self.log.info(datalist)
        self.log.info(dbhash_list)
        return dbhash_list

    def __validate_data_hash(self, backup_hash, restore_hash):
        """
        Validates db hash
        Args:
            backup_hash     (dict)      --  hash of backup databases
            restore_hash    (dict)      --  hash of restore databases
        """
        self.log.info("*********Validating db hash*********")
        restore_databases = restore_hash.keys()
        backup_databases = backup_hash.keys()
        for database in restore_databases:
            if database in backup_databases:
                if restore_hash[database]['md5'] is None:
                    # for collection level restore when rename_destination was enabled database md5
                    # hash value changes, to avoid verification failure issue this if is used
                    restore_hash[database]['md5'] = backup_hash[database]['md5']
                if backup_hash[database] == restore_hash[database]:
                    self.log.info(f"Database: {database} hash value verified successfully.")
                else:
                    self.log.info(f"Database: {database} hash value verification failed.")
                    diffkeys = [key for key in backup_hash[database] if backup_hash[database][
                        key] != restore_hash[database][key]]
                    self.log.info(f"{diffkeys} are the different keys in backup and restore hash")
                    for key in diffkeys:
                        self.log.info(f"{database}_{key} : {backup_hash[database][key]} '--->' "
                                      f"{restore_hash[database][key]}")
                    raise Exception("db hash validation failed.")
            else:
                self.log.info(f"Database: {database} doesn't exist in backup databases.")
        self.log.info("*********db hash validation succesfull*****************")

    def validate_restore(self, datalist, destination_host,
                         destination_port, user='',
                         passwd='', dbname="admin",
                         backup_hash=None, replicaset=None):
        """Validate restore.

        Args:
            datalist                        (list) -- data to be validated
            destination_host                (str)  -- destination client
            destination_port                (int)  -- destination mongod port
            user                            (str)  -- DB user
            passwd                          (str)  -- DB password
            dbname                          (str)  -- authentication database
                   default value :admin
            backup_hash                     (dict) -- hash of backup databases
                   default value :None
            replicaset                      (str) --  replica set
        Returns:
                (boolean)  -- true on success, false on failure
        """
        try:
            self.log.info("Validate restore")
            databases = datalist.keys()
            # collectionlist=datalist.values()
            dest_cl_machine = self.commcell.clients.get(destination_host)
            destination_host = str(dest_cl_machine.client_hostname)
            if self.atlas == 1:
                db_connection = pymongo.MongoClient(self.connection_string, tlsCAFile=certifi.where()) or None
            else:
                if replicaset is not None:
                    db_connection = pymongo.MongoClient(destination_host, port=destination_port,
                                                        username=user, password=passwd, authSource=dbname,
                                                        replicaSet=replicaset)
                else:
                    db_connection = pymongo.MongoClient(destination_host, port=destination_port,
                                                        username=user, password=passwd, authSource=dbname)
            # db=dbConnection["admin"]
            self._connection = db_connection
            database_names = db_connection.list_database_names()
            for dbs in databases:
                if dbs in database_names:
                    dbcollectionlist = datalist[dbs]
                    number_docs = dbcollectionlist.pop()
                    newdbcon = db_connection[dbs]
                    collection_names = newdbcon.list_collection_names()
                    for collection in dbcollectionlist:
                        if collection in collection_names:
                            colcon = newdbcon[collection]
                            if number_docs == colcon.count_documents({}):
                                self.log.info("Document count matched for "
                                              "collection :" + collection + " in database :" + dbs)
                            else:
                                self.log.info("Document count did not match for "
                                              "collection :" + collection + " in database :" + dbs)
                                return False
                        else:
                            self.log.info("collection: " +
                                          collection + "does not exist in the database: " + dbs)
                            return False
                else:
                    self.log.info("Database : %s is not present in the server", dbs)
                    return False
            if backup_hash:
                restore_hash = self.get_data_hash(datalist, db_connection)
                self.__validate_data_hash(backup_hash, restore_hash)
            self.log.info("*********validation succesfull*****************")
            return True
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception("Exception in validation:{0}".format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("Exception in validation:{0}".format(str(exception_case)))

    def start_mongos_service_using_script(self, startcmd):
        """Start mongos server as a script.

        Args:
            startcmd                           (str)  --  mongos start command

        """
        try:
            self.log.info("Start mongos service using script")
            client = self.commcell.clients.get(self.host_name)
            client_obj = Machine(client)
            controller_obj = Machine()
            if client_obj.os_info == 'UNIX':
                config_file = "startMongosServer.sh"
                local_config_path = controller_obj.join_path(constants.TEMP_DIR, config_file)
                remote_path = client_obj.join_path(client.install_directory, "Base")
                remote_path = client_obj.join_path(remote_path, "TempConfig")
                client_obj.create_directory(remote_path)
                file_path = open(local_config_path, 'w', newline='\n')
                if startcmd is not None:
                    file_path.write(startcmd)
                    self.log.info("Start command: %s", startcmd)
            else:
                config_file = "startMongosServer.bat"
                local_config_path = controller_obj.join_path(constants.TEMP_DIR, config_file)
                remote_path = client_obj.join_path(client.install_directory, "Base")
                remote_path = client_obj.join_path(remote_path, "TempConfig")
                if client_obj.check_directory_exists(remote_path):
                    client_obj.remove_directory(remote_path)
                client_obj.create_directory(remote_path)
                file_path = open(local_config_path, 'w')
                if startcmd is not None:
                    service_name = "mongos__automation"
                    cmd_to_delete = "sc delete {0}".format(service_name)
                    cmd_to_create = "{0} --install --serviceName {1} " \
                                    "--serviceDisplayName" \
                                    " {2}".format(startcmd, service_name,
                                                  "mongos__automation")
                    cmd_to_start = "net start {0}".format(service_name)
                    file_path.write(cmd_to_delete + "\n" + cmd_to_create + "\n" + cmd_to_start)
                    self.log.info("Start commands: %s , %s ,%s"
                                  "", cmd_to_delete, cmd_to_create, cmd_to_start)
            file_path.close()
            copy_status = client_obj.copy_from_local(local_config_path, remote_path)
            self.log.info("copy_status :%s", copy_status)
            if copy_status is False:
                raise Exception("Failed to copy file to remote machine.Exiting")
            if client_obj.os_info == 'UNIX':
                remote_config_file = client_obj.join_path(remote_path, "startMongosServer.sh")
                exitcode, output, error = client.execute_script(
                    script_type="UnixShell", script=remote_config_file, wait_for_completion=True)
                self.log.info("Start mongod output --> exitcode: %s,output: %s,"
                              "error: %s", str(exitcode), output, error)
            else:
                remote_config_file = client_obj.join_path(remote_path, "startMongosServer.bat")
                exitcode, output, error = client.execute_script(script_type="WindowsBatch",
                                                                script=remote_config_file,
                                                                wait_for_completion=True)
                self.log.info("cmd:Running windows batch script, exitcode: %s,output: %s,"
                              "error: %s", str(exitcode), output, error)
            if exitcode == 0:
                self.log.info("successfully started mongod server on %s using "
                              "start command %s", str(client), startcmd)
            elif exitcode == 48:
                self.log.info("Service is already runningon %s using "
                              "start command %s", str(client), startcmd)
            else:
                self.log.info("Failed to start mongod server on %s using"
                              " start command %s", str(client), startcmd)
                self.log.info("exitcode: %s,output: %s,"
                              "error: %s", str(exitcode), output, error)
            controller_obj.delete_file(remote_config_file)
        except pymongo.errors.AutoReconnect as exception_case:
            self.log.info("Exception: %s", str(exception_case))
            self.log.info("Please start the server manually")
            pass
        except Exception as exception_case:
            self.log.info("Exception: %s", str(exception_case))
            self.log.info("Please start the server manually")
            pass

    def delete_test_data(self, prefix="auto_db"):
        """Deletes databases that start with given prefix
        Args:
            prefix                 (str)  --  database name prefix
        """
        self.log.info("Deleting databases that start with prefix: %s", prefix)
        db_list = self.get_db_list()
        for database in db_list:
            if database.startswith(prefix):
                self.__drop_db(database)
        self.log.info("successfully deleted databases that started with prefix: %s", prefix)

    def check_if_single_node_replicaset_from_DB(self, pseudoclient):
        """Check if the server type of the single node replica set instance is 4
        Args:
            pseudoclient                  (str) -- pseudoclient name
        Returns:
                                          (bool) -- true if single node replica set
                                                    false otherwise
        """
        try:
            self.log.info("Checking if the server is identified as a single node replica set")
            pclient = self.commcell.clients.get(pseudoclient)
            agent = pclient.agents.get('big data apps')
            instancelist = agent.instances.all_instances
            instanceid = instancelist[pclient.client_name]
            query = "select attrVal from app_instanceprop where componentNameId={0} and" \
                    " attrName like '%MongoDB Server Type%'".format(instanceid)
            self.csdb.execute(query)
            self.log.info("%s executed", query)
            result = self.csdb.fetch_one_row()
            result = result[0]
            self.log.info("result: %s", str(result))
            if int(result) == 4:
                return True
            else:
                return False
        except pymongo.errors.AutoReconnect as exception_case:
            raise Exception("Exception: {0}".format(str(exception_case)))
        except Exception as exception_case:
            raise Exception("unable to identify if it is a single node "
                            "replica set:{0}".format(str(exception_case)))

    def check_if_sharded_cluster(self):
        """Check if the cluster is a sharded cluster"""
        try:
            db = self._connection["admin"]
            db.command({"isdbgrid": 1})
            return 0
        except Exception as x:
            if 'no such command' in str(x):
                self.log.info("This cluster is not a sharded cluster")
                return 1

    def check_if_replica_set(self):
        """Check if the cluster is a replica set"""
        try:
            collection = self._connection.local.system.replset
            doc = collection.find()[0]
            self.log.info(doc['_id'] + ":replica set name identified."
                                       " This is a replica set cluster")
            return True
        except Exception as e:
            self.log.info("local.system.replset doesn't exist: " + str(e))
            return False

    def check_single_node_replica_set(self):
        """Check if the cluster is a single node replica set"""
        try:
            collection = self._connection.local.system.replset.find()[0]
            nodenums = len(collection['members'])
            db = self._connection["admin"]
            masterop = db.command({"ismaster": 1})
            ismaster = masterop['ismaster']
            self.log.info("Output of ismaster:" + str(ismaster) + " and number of nodes:" + str(nodenums))
            if ismaster and nodenums == 1:
                return True
            else:
                return False
        except Exception as e:
            self.log.info("There is an exception while trying to check if the server "
                          "is a single node replica set")

class MongoAgentHelper():
    """
    Helper class for Mongo DB agent related operations.
    """

    def __init__(self, tc_object):
        """
        Initializes the MongoAgentHelper object

        Args:
           tc_object  (obj)  --  instance of testcase

        Returns:
           object  --  instance of MongoAgentHelper class

        """
        self.client_machine = None
        self.client_object = None
        self.tc_object = tc_object
        self.mongodb_object = tc_object
        self.app_name = self.__class__.__name__
        self.commcell = self.tc_object.commcell
        self.tcinputs = self.tc_object.tcinputs
        self.log = self.tc_object.log
        self.client_name = tc_object.client
        self.agentname = "Big Data Apps"
        self.client = None
        self.csdb = self.tc_object.csdb
        self.backupsetname = tc_object.tcinputs.get("BackupSetName", "defaultBackupSet")
        self.subclientname = tc_object.tcinputs.get("SubclientName", "default")
        self.client_name = ""
        self.master_node = ""
        self.master_hostname = ""
        self.os_user = ""
        self.plan = ""
        self.port = ""
        self.bin_path = ""
        self.db_user = ""
        self.db_password = ""
        self.masteruri = ""
        self.populate_tc_inputs(tc_object)
        self.log.info("CVoperation Class Initilized ")


    def populate_tc_inputs(self, tc_object):
        """
        Initializes all the test case inputs after validation

        Args:
            tc_object (obj)    --    Object of testcase

        Raises:
            Exception:
                if a valid CVTestCase object is not passed.

                if CVTestCase object doesn't have agent initialized
        """
        if not isinstance(tc_object, CVTestCase):
            raise Exception("Valid test case object must be passed as argument")
        self.client_name = tc_object.tcinputs.get("ClientName")
        self.master_node = tc_object.tcinputs.get("MasterNode")
        self.master_hostname = tc_object.tcinputs.get("MasterHostName")
        self.os_user = tc_object.tcinputs.get("UserName")
        self.plan = tc_object.tcinputs.get("Plan")
        self.port = tc_object.tcinputs.get("Port")
        self.replicaset= self.tcinputs.get("ReplicaSetName")
        self.primary_host= self.tcinputs.get("PrimaryHost")
        self.bin_path = tc_object.tcinputs.get("BinPath")
        self.db_user = tc_object.tcinputs.get("DB_user")
        self.db_password = tc_object.tcinputs.get("DB_password")
        self.bkp_dir_path= tc_object.tcinputs.get("backupDataDir")
        self.log = tc_object.log
        self.client_machine = Machine(self.commcell.clients.get(self.primary_host),
                                      self.commcell)
        self.client_object = self.commcell.clients.get(self.client_name)
        self._agent_object= self.client_object.agents.get("big data apps")
        self._instance_object = self._agent_object.instances.get(
            self.client_name)


    def add_mongodb_pseudo_client(self):
        """
        Adds a new MongoDB Pseudo client Using cvpysdk object

        Args:
            Nothing
        Returns:
            Client -- Client object of newly created MongoDB Pseudo client
        """

        if self.commcell.clients.has_client(self.client_name):
            self.log.info('Client Exists , Deleting and Recreating ')
            # self.commcell.clients.delete(self.new_client_name)
        if self.db_user == 'None':
            self.client = self.commcell.clients.add_mongodb_client(
                self.client_name, self.master_node, self.master_hostname, self.port,
                self.os_user, self.bin_path, self.plan)
        else:
            self.client = self.commcell.clients.add_mongodb_client(
                self.client_name, self.master_node, self.master_hostname, self.port,
                self.os_user, self.bin_path, self.plan, self.db_user, self.db_password)
        return self.client


    def discover_mongodb_nodes(self, instance_id):

        """
        Runs Nodes Discover operation on Pseudo client

        Args:
            instance_id -- instance id of Instance where discover needs to run
        Returns:
            response received from Discover API
        """

        self.log.info("Starting Discover on the Instance")

        master_obj = self.commcell.clients.get(self.master_node)
        master_client_id = int(master_obj.client_id)
        # master_obj -- Object of Master node belonging to client
        # client_id -- client id of master Node

        if self.db_user == 'None':
            discover_response = self._instance_object.discover_mongo_nodes(instance_id,
                                                                           self.master_node,
                                                                           self.master_hostname,
                                                                           master_client_id, self.port)
        else:
            discover_response = self._instance_object.discover_mongodb_nodes(instance_id,
                                                                             self.master_node,
                                                                             self.master_hostname,
                                                                             master_client_id,
                                                                             self.port,
                                                                             self.bin_path,
                                                                             self.db_user,
                                                                             self.os_user)
        return discover_response

    def run_mongodb_snap_backup(self, client_object, subclient_details=None, backup_type="Full"):

        """
        Runs Full backup on the specified mongodb Client

        Runs Full backup by default as we only support Interactive Full snap backups
        Args:
            client object : client object for the instance where backup needs to run
            subclient_details: Subclient details on extra parameters.
            backup_type: Default (FULL)

        Returns :
           tuple: A tuple containing two elements:
                  - str: The job ID of the primary backup job.
                  - str or None: The job ID (as a string) of the backup copy job.
        """

        self.log.info("Starting Full Snap Backup on the Pseudo client")
        if subclient_details is None:
            req_agent = client_object.agents.get("big data apps")
            req_backupset = req_agent.backupsets.get("defaultbackupset")
            req_subclient = req_backupset.subclients.get("default")
        else:
            req_subclient = subclient_details
        jm_obj = JobManager()

        job_obj = req_subclient.backup(backup_type)
        print(job_obj)
        self.log.info("Waiting For Completion Of Snap Backup Job With Job ID: %s",
                      str(job_obj.job_id))
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed To Run Snap Backup {0} With Error {1}".format(
                    str(job_obj.job_id), job_obj.delay_reason
                )
            )

        if not job_obj.status.lower() == "completed":
            raise Exception(
                "Job {0} is not completed and has job status: {1}".format(
                    str(job_obj.job_id), job_obj.status
                )
            )
        self.log.info(
            "Successfully Finished Snap Backup Job %s", str(job_obj.job_id)
        )
        time.sleep(10)
        self.jm = JobManager(commcell=self.commcell)
        jobs = self.jm.get_filtered_jobs(
            self.client_name,
            job_filter='Backup',
            time_limit=10,
            retry_interval=5
        )
        print(jobs)
        backup_copy_job_id = jobs[1][0]
        self.log.info ("Backup Copy Job ID %s ", backup_copy_job_id)
        snap_jobid = job_obj.job_id
        return snap_jobid, backup_copy_job_id

    def run_mongodb_inplace_restore(self, client_object):
        """
        Runs inplace restore  for the MongoDB Instance
        Args:
            client object : client object for the instance where restore needs to run

        """

        self.log.info("Starting  inplace restore")

        req_agent = client_object.agents.get("big data apps")
        req_backupset = req_agent.backupsets.get("defaultbackupset")
        req_subclient = req_backupset.subclients.get("default")
        self.log.info("Sending browse request and starting inplace restore ")
        data = req_subclient.browse_mongodb(self.master_node)
        self.log.info (" Browse returned on subclient is : %s", str(data))
        job_obj = req_subclient.restore_mongodb(data,self.master_node)
        self.log.info("Waiting For Completion Of RestoreJob With Job ID: %s",
                      str(job_obj.job_id))
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed To Run Restore job {0} With Error {1}".format(
                    str(job_obj.job_id), job_obj.delay_reason
                )
            )

        if not job_obj.status.lower() == "completed" :
            raise Exception(
                "Job {0} is not completed and has job status: {1}".format(
                    str(job_obj.job_id), job_obj.status
                )
            )
        self.log.info(
            "Successfully Finished Restore Job %s", str(job_obj.job_id)
        )

    def run_full_cluster_restore(self):
        """Restores FULL database and verify the restored data
        Args:
            srcdbname        (str)    --    source database name
            destdbname       (str)    --    destination database name

            wait_to_complete  (bool)  --  Specifies whether to wait until restore job finishes.
        """

        restore_dict = {}
        restore_dict["no_of_streams"] = 2
        restore_dict["multinode_restore"] = True
        restore_dict["destination_instance"] = self.client_name
        restore_dict["destination_instance_id"] = self._instance_object.instance_id
        restore_dict["paths"] = ["/"]
        restore_dict["mongodb_restore"] = True
        restore_dict["destination_client_id"] = self.client_object.client_id
        restore_dict["destination_client_name"] = self.client_object.client_name
        restore_dict["overwrite"] = True
        restore_dict["client_type"] = 29
        restore_dict["destination_appTypeId"] = 64
        restore_dict["backupset_name"] = self.backupsetname
        restore_dict["_type_"] = 5
        restore_dict["subclient_id"] = -1
        restore_dict["source_shard_name"] = self.replicaset
        restore_dict["destination_shard_name"] = self.replicaset
        restore_dict["hostname"] = self.primary_host
        restore_dict["clientName"] = self.master_node
        restore_dict["desthostName"] = self.primary_host
        restore_dict["destclientName"] = self.master_node
        restore_dict["destPortNumber"] = self.port
        restore_dict["destDataDir"] = self.bin_path
        restore_dict["bkpDataDir"] = self.bkp_dir_path
        restore_dict["backupPortNumber"] = self.port
        restore_dict["restoreDataDir"] = self.bkp_dir_path
        restore_dict["primaryPort"] = self.port

        self.log.info("Running full cluster restore")
        job_object = self._instance_object.restore(
            restore_options=restore_dict)
        self.log.info(
            "wait for restore job %s to complete",
            job_object._job_id)

        job_object.wait_for_completion()
        if not job_object.status.lower() == "completed":
            raise Exception(
                "Job {0} is not completed and has job status: {1}".format(
                    str(job_object.job_id), job_object.status
                )
            )
        self.log.info(
            "Successfully Finished Restore Job %s", str(job_object.job_id)
        )
        return job_object.job_id


    def validate_bigdata_app_list(self, client_obj):
        """
        Validates if the client exists in Big Data Apps List

        Args:
            client_obj              (Object)    --      MongoDB  client object

        Returns:
            instance ID
        """
        agent_obj = client_obj.agents
        req_agent = agent_obj.get("big data apps")
        instance_obj = req_agent.instances
        all_instances = instance_obj.all_instances

        if self.client_name.lower() in all_instances.keys():
            instance_id = all_instances[self.client_name.lower()]
            return instance_id

        raise Exception("Failed to find required client in big data entities")

    def get_client_jobs(self, client_name: str) -> dict:
        """
        Util to Get client jobs using qcommand to verify java GUI jobs listing

        Args:
            client_name (str)   -   name of client to view job history for

        Returns:
            client_jobs (dict)  -   dict of jobs of client with job id key and other data value
                                    as would be visible in java console
        """
        if not self.commcell.clients.has_client(client_name):
            self.log.info(f"client {client_name} not found, so no jobs")
            return {}
        gui_resp = self.commcell.execute_qcommand(
            f'qlist jobhistory -c {client_name}'
        )
        lines = gui_resp.text.split('\n')
        table = [line.split() for line in lines if line and '--' not in line]
        headers = table[0]
        data = {}
        for row in table[1:]:
            job_id = row[headers.index('JOBID')]
            data[job_id] = {
                headers[col_idx]: row[col_idx]
                for col_idx in range(len(headers))
                if headers[col_idx] != 'JOBID'
            }
        return data

    def get_logs_for_job_from_file(self, job_id, log_file_name, search_term=None):
        """From a log file object only return those log lines for a particular job ID.

        Args:
            client_obj      (obj)   -- client obj where we need to search for term.

            job_id          (str)   --  Job ID for which log lines need to be fetched.

            log_file_name   (bool)  --  Name of the log file.

            search_term     (str)   --  Only capture those log lines containing the search term.

        Returns:
            str     -   \\r\\n separated string containing the requested log lines.

            None    -   If no log lines were found for the given job ID or containing the given search term.

        Raises:
            None

        """

        # GET ONLY LOG LINES FOR A PARTICULAR JOB ID

        return self.client_machine.get_logs_for_job_from_file(job_id, log_file_name, search_term)

    def verify_cluster_restore(self, content):

        """
        Validate cluster post restore all content

        Args:
            content (dict)   -   Test Data uploaded dictionary

        raise exception if anything validation fails.

        """

        data_object = MongoDBHelper(self,
                                         masterhostname=self.master_hostname,
                                         port=self.tcinputs.get("Port"))

        db_list = data_object.get_db_list()
        cluster_collections_list=[]
        databases_list = list(content.keys())
        collection_list = [item for sublist in content.values() for item in sublist]
        collection_list = [item for item in collection_list if not isinstance(item, int)]
        self.log.info("database list %s", str(databases_list))
        self.log.info("collectionList %s", str(collection_list))

        for element in databases_list:
            if element in db_list:
                self.log.info(f"database {element} is in cluster")
            else:
                self.log.info(f"Database {element} not in cluster.")
                raise Exception("Element not in list")
        for db in databases_list:
            coll_list = data_object.get_collection_list(db)
            cluster_collections_list.extend(coll_list)

        for element in collection_list:
            if element in cluster_collections_list:
                self.log.info(f"collection {element} is in cluster")
            else:
                self.log.info(f"collection {element} not in cluster")
                raise Exception("collection is missing ")
