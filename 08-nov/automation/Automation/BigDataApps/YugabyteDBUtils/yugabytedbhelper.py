# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for yugabyteDB cluster related operations.
Classes defined in this file:
    yugabyteDBHelper:         Class for connecting to yugabyteDB cluster and performing db queries.
        __init__()                 --  Constructor for creating a connection to yugabyteDB cluster
        _connect_to_ysqlsh         --  create cluster object and initiate the ysqlsh connection
        _connect_to_ycqlsh         --  create cluster object and initiate the ycqlsh connection
        connection()               --  return the yugabyteDB cluster connection object
        create_ysql_database()     --  execute db query to create a sql test database
        create_ycql_database()     --  execute db query to create a cql test keyspace
        drop_ysql_database()       --  execute db query to drop a sql test database
        drop_ycql_database()       --  execute db query to drop a cql test keyspace
        create_ysql_table()        --  execute db query to create a ysql table
        create_ycql_table()        --  execute db query to create a ycql table
        drop_ysql_table()          --  execute db query to drop ysql table
        drop_ycql_table()          --  execute db query to drop ycql table
        add_ysql_data()            --  add test data to ysql table
        add_ycql_data()            --  add test data to ycql table
        update_ysql_data()         --  update ysql table data
        update_ycql_data()         --  update ycql table data
        get_ysql_rows()            --  get ysql table rows
        get_ycql_rows()            --  get ycql table rows
        close_connection()         --  close the db connection

    yugabyteDB:                  Class for creating/deleting instances and running backup/restore
                                 for yugabyteDB instance Under Big data, It also has the methods to
                                 connect/disconnect to cql host, generate/modify/drop test data
                                 and validate restored data
        __init__()                                      --      constructor for creating yugabyteDB object
        connect_to_db()                                 --      connect to yugabytedb cluster
        populate_test_data()                            --      populate test data
        update_test_data()                              --      update test data
        add_credential()                                --      adds s3 credential
        add_yugabyte_client()                           --      adds a new yugabytedb client
        get_client_details()                            --      fetches the details of the yugabytedb client
        run_backup()                                    --      initiate backup job and verify backup job complete
        verify_restore()                                --      verify restore job and validate the restored data
        run_restore()                                   --      initiate restore job and verify restore job completed
        validate_restoredata()                          --      verified expected data are restored to yugabyteDB
                                                                cluster db
        drop_db_restore()                               --      drops database and restores with same db name
        restore_to_newdb()                              --      restores to a new database name
        new_table_restore()                             --      restores new table
        drop_database()                                 --      drops sql and cql test database
        drop_table()                                    --      drops sql and cql table
        delete_yugabyte_client()                       --      deletes the yugabyte client
        close_dbconnection()                            --      shuts down yugabyteDB db connection
"""

import requests
import time
import psycopg2
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from ssl import SSLContext, PROTOCOL_TLS_CLIENT, CERT_REQUIRED
from AutomationUtils import logger
from cvpysdk.credential_manager import Credentials
from cvpysdk.client import Clients
from cvpysdk.agent import Agent
from cvpysdk.backupset import Backupset
from cvpysdk.subclient import Subclient


class YugabyteDBHelper():
    """Class for performing commvault operations"""

    def __init__(self,node_ip,
            ycql_username,
            ycql_password,
            ysql_username,
            ysql_password,
            sslrootcert):
        """
        Initializes the CvOperation object by calling commcell object of cvpysdk.

        Args:
           yugabytedb_object  (obj)  --  instance of yugabytedb class

        Returns:
           object  --  instance of CvOperation class

        """
        """self.tc_object = yb_object.tc_object
        self.yb_object = yb_object
        self.commcell = self.tc_object.commcell
        self.tcinputs = self.tc_object.tcinputs
        self.instanceName = yb_object.instanceName
        self.log = self.tc_object.log
        self.log.info("Cvoperation class initialized")"""
        self.node_ip = node_ip
        self.ycql_username = ycql_username
        self.ycql_password = ycql_password
        self.ysql_username = ysql_username
        self.ysql_password = ysql_password
        self.sslrootcert = sslrootcert
        self._cluster = None
        self._connection = None
        self._cursor = None
        self._connect_to_ycqlsh()
        self.log = logger.get_log()

    @property
    def connection(self):
        """return yugabyteDB cluster connection object"""
        return self._connection

    def _connect_to_ysqlsh(self):
        """initiate Cluster object and connect to yugabyteDB cluster ysqlsh"""
        try:
            self._connection = psycopg2.connect(
                host=self.node_ip,
                dbname='yugabyte',
                port=5433,
                user=self.ysql_username,
                password=self.ysql_password)
            self._cursor = self._connection.cursor()
            return self._cursor
            self.log.info("yugabytedb cluster ysqlsh connection created")
        except Exception as excp:
            raise Exception(
                'Failed to connect to yugabytedb ysqlsh\nERror: "{0}"'.format(excp))

    def _connect_to_ycqlsh(self):
        """initiate cluster object and connect to yugabytedb cluster ycqlsh"""
        try:
            ssl_context = SSLContext(PROTOCOL_TLS_CLIENT)
            ssl_context.load_verify_locations(self.sslrootcert)
            cluster = Cluster(contact_points=[self.node_ip],
                              ssl_context=ssl_context,
                              ssl_options={'server_hostname': self.node_ip},
                              auth_provider=PlainTextAuthProvider(username=self.ycql_username,
                                                                  password=self.ycql_password))
            self._session = cluster.connect()
            return self._session
            self.log.info("yugabytedb cluster ycqlsh connection created")
        except Exception as excp:
            raise Exception(
                'Failed to connect to yugabytedb ycqlsh\nERror: "{0}"'.format(excp))

    def create_ysql_database(self, sqldbname):
        """
        create sql database
        Args:
            sqldbname (str)        -- ysql database name to be created
        """
        with self._connect_to_ysqlsh() as curs:
            cmd = "CREATE DATABASE " + sqldbname
            curs.execute("ROLLBACK")
            curs.execute(cmd)
            self._connection.commit()
            self.log.info(
                "create_database: status message: %s",
                curs.statusmessage)

    def create_ycql_database(self, cqldbname):
        """
        create cql keyspace
        Args:
            cqldbname (str)        -- cql keyspace name to be created
        """
        with self._connect_to_ycqlsh() as curs:
            cmd = "CREATE KEYSPACE IF NOT EXISTS " + cqldbname + ";"
            curs.execute(cmd)
            self.log.info("created ycql keyspace %s", cqldbname)

    def drop_ysql_database(self, sqldbname):
        """
        drop sql database
        Args:
            sqldbname (str)        -- sql database name to be dropped
        """
        with self._connect_to_ysqlsh() as curs:
            curs.execute("ROLLBACK")
            cmd = "SELECT pg_terminate_backend(pid) \
            FROM pg_stat_activity WHERE pid <> pg_backend_pid() " \
                  "AND datname = '" + sqldbname + "';"
            curs.execute(cmd)
            cmd = "DROP DATABASE IF EXISTS " + sqldbname
            curs.execute(cmd)
            self._connection.commit()
            self.log.info(
                "drop_database: status message: %s",
                curs.statusmessage)

    def drop_ycql_database(self, cqldbname, tbname):
        """
        drop ycql keyspace
        Args:
            cqldbname (str)        -- cql keyspace name to be dropped
            tbname (str)           -- cql table name to be dropped before dropping keyspace
        """
        with self._connect_to_ycqlsh() as curs:
            cmd = "DROP table IF EXISTS " + cqldbname + '.' + tbname
            curs.execute(cmd)
            self.log.info("dropped table %s", tbname)
            cmd = "DROP keyspace IF EXISTS " + cqldbname
            curs.execute(cmd)
            self.log.info("dropped database %s", cqldbname)

    def create_ysql_table(self, sqldbname, tbname):
        """
        create sql table
        Args:
            sqldbname (str)     -- sql database name
            tbname (str)        -- sql table name to be created
        """
        self._connection = psycopg2.connect(
            host=self.node_ip,
            dbname=sqldbname,
            port=5433,
            user=self.ysql_username,
            password=self.ysql_password)
        with self._connection.cursor() as curs:
            cmd = "CREATE TABLE IF NOT EXISTS " + \
                  tbname + "(id INT PRIMARY KEY, name TEXT)"
            curs.execute(cmd)
            self._connection.commit()
            self.log.info(
                "create_table: status message: %s",
                curs.statusmessage)

    def create_ycql_table(self, cqldbname, tbname):
        """
        creates cql table
        Args:
            dbname (str)        -- cql keyspace name
            tbname (str)        -- cql table name to be created
        """
        with self._connect_to_ycqlsh() as curs:
            cmd = "CREATE TABLE IF NOT EXISTS " + cqldbname + "." + \
                  tbname + "(id INT PRIMARY KEY, name TEXT)"
            curs.execute(cmd)
            self.log.info("created table %s", tbname)

    def drop_ysql_table(self, sqldbname, tbname):
        """
        drop sql table
        Args:
            sqldbname (str)     -- sql database name
            tbname (str)        -- sql table name to be dropped
        """
        self._connection = psycopg2.connect(
            host=self.node_ip,
            dbname=sqldbname,
            port=5433,
            user=self.ysql_username,
            password=self.ysql_password)
        with self._connection.cursor() as curs:
            cmd = "DROP TABLE " + tbname
            curs.execute(cmd)
            self._connection.commit()
            self.log.info("drop_table: status message: %s", curs.statusmessage)

    def drop_ycql_table(self, cqldbname, tbname):
        """
        drop cql table
        Args:
            cqldbname (str)     -- cql keyspace name
            tbname (str)        -- cql table name to be dropped
        """
        with self._connect_to_ycqlsh() as curs:
            cmd = "DROP TABLE " + cqldbname + "." + tbname
            curs.execute(cmd)
            self._connection.commit()
            self.log.info("dropped cql table %s", tbname)

    def add_ysql_data(self, sqldbname, tbname, ids):
        """
        add data into sql tables
        Args:
            sqldbname (str)     -- sql database name
            tbname (str)        -- sql table name
            ids    (list)       -- list of row ids
        """
        self._connection = psycopg2.connect(
            host=self.node_ip,
            dbname=sqldbname,
            port=5433,
            user=self.ysql_username,
            password=self.ysql_password)
        with self._connection.cursor() as curs:
            for testid in ids:
                cmd = "insert into " + tbname + \
                      "(id, name) values(" + str(testid) + ", 'name')"
                curs.execute(cmd)
                self.log.info(
                    "insert_data: id: %s, status message: %s",
                    testid,
                    curs.statusmessage)
            self._connection.commit()

    def add_ycql_data(self, cqldbname, tbname, ids):
        """
        add data into cql tables
        Args:
            cqldbname (str)     -- cql database name
            tbname (str)        -- cql table name
            ids    (list)       -- list of row ids
        """
        with self._connect_to_ycqlsh() as curs:
            for testid in ids:
                cmd = "insert into " + cqldbname + "." + tbname + \
                      "(id, name) values(" + str(testid) + ", 'name')"
                curs.execute(cmd)
                self.log.info("inserted data into cql table")

    def update_ysql_data(self, sqldbname, tbname, ids, deletedata=False):
        """
        update sql test data
        Args:
            sqldbname (str)        -- sql database name
            tbname (str)           -- sql table name
            ids    (list)          -- list of row ids
            deletedata (boolean)   -- delete the table rows if True, otherwise add new rows
        """
        self._connection = psycopg2.connect(
            host=self.node_ip,
            dbname=sqldbname,
            port=5433,
            user=self.ysql_username,
            password=self.ysql_password)
        with self._connection.cursor() as curs:
            for testid in ids:
                cmd_update = "insert into " + tbname + \
                             "(id,name)values(" + str(testid) + ",'name1')"
                cmd_delete = "delete from " + tbname + \
                             " where id=" + str(testid)
                if deletedata:
                    curs.execute(cmd_delete)
                else:
                    curs.execute(cmd_update)
                self.log.info(
                    "update_row: id: %s, status message: %s",
                    testid,
                    curs.statusmessage)
            self._connection.commit()

    def update_ycql_data(self, cqldbname, tbname, ids, deletedata=False):
        """
        update cql test data
        Args:
            cqldbname (str)        -- cql database name
            tbname (str)           -- cql table name
            ids    (list)          -- list of row ids
            deletedata (boolean)   -- delete the table rows if True, otherwise add new rows
        """
        with self._connect_to_ycqlsh() as curs:
            for testid in ids:
                cmd_update = "update " + cqldbname + "." + tbname + \
                             " set name='name1' where id=" + str(testid)
                cmd_delete = "delete from " + cqldbname + \
                             "." + tbname + " where id=" + str(testid)
                if deletedata:
                    curs.execute(cmd_delete)
                else:
                    curs.execute(cmd_update)
                self.log.info("updated ycql table rows")

    def get_ysql_rows(self, sqldbname, tbname):
        """
        get sql rows ResultSet from table {tbname} in database {dbname}
        Args:
                sqldbname (str)     -- sql database name
                tbname (str)        -- sql table name
            Return:
                ResultSets for rows in table
        """
        self._connection = psycopg2.connect(
            host=self.node_ip,
            dbname=sqldbname,
            port=5433,
            user=self.ysql_username,
            password=self.ysql_password)
        with self._connection.cursor() as curs:
            cmd = "SELECT id, name FROM " + tbname + " order by id"
            curs.execute(cmd)
            return curs.fetchall()

    def get_ycql_rows(self, cqldbname, tbname):
        """
        get cql rows ResultSet from table {tbname} in database {dbname}
        Args:
                cqldbname (str)     -- cql keyspace name
                tbname (str)        -- cql table name
            Return:
                ResultSets for rows in table
        """
        with self._connect_to_ycqlsh() as curs:
            cmd = "SELECT id, name FROM " + cqldbname + "." + tbname
            rows = curs.execute(cmd)
            data = []
            for i in rows:
                row = (i.id, i.name)
                data.append(row)
            return data

    def close_connection(self):
        """close the connection to yugabyteDB cluster"""
        self._connection.close()


class YugabyteDB:
    """
        class has the functions to operate YugabyteDB instances Under BigData Apps
        """

    def __init__(self, testcase):
        """Constructor for creating the yugabyteDB object"""
        self.__commcell = testcase.commcell
        self.__yugabytedb = None
        self.log = logger.get_log()
        self._credentials_object = Credentials(self.__commcell)
        self.data_access_nodes = testcase.tcinputs.get("data_access_nodes")
        self.db_host = testcase.tcinputs.get("db_host")
        self.node_ip = testcase.tcinputs.get("node_ip")
        self.plan_name = testcase.tcinputs.get("plan_name")
        self.api_token = testcase.tcinputs.get("api_token")
        self.universe_name = testcase.tcinputs.get("universe_name")
        self.config_name = testcase.tcinputs.get("config_name")
        self.kms_config = testcase.tcinputs.get("kms_config")
        self.user_uuid = testcase.tcinputs.get("user_uuid")
        self.universe_uuid = testcase.tcinputs.get("universe_uuid")
        self.config_uuid = testcase.tcinputs.get("config_uuid")
        self.kmsconfig_uuid = testcase.tcinputs.get("kmsconfig_uuid")
        self.restore_no_of_stream = testcase.tcinputs.get("RestoreNoOfStream", 2)
        self.agentname = "Big Data Apps"
        self.backupsetname = testcase.tcinputs.get("BackupSetName", "defaultBackupSet")
        self.subclientname = testcase.tcinputs.get("SubclientName", "default")
        self.ysql_username = testcase.ysql_username
        self.ysql_password = testcase.ysql_password
        self.ycql_username = testcase.ycql_username
        self.ycql_password = testcase.ycql_password
        self.aws_access_key = testcase.aws_access_key
        self.aws_secret_key = testcase.aws_secret_key
        self.instance_name = "YUGABYTE_" + testcase.id
        self.credential_name = "credential_" + testcase.id
        self.sslrootcert = testcase.sslrootcert
        self.sqldbname = testcase.sqldbname
        self.cqldbname = testcase.cqldbname
        self.destsqldbname = testcase.destsqldbname
        self.destcqldbname = testcase.destcqldbname
        self.content = testcase.content
        self.client = None

    def connect_to_db(self):
        """initiate yugabytedb connection """
        self.__yugabytedb = YugabyteDBHelper(
            node_ip=self.node_ip,
            ycql_username=self.ycql_username,
            ycql_password=self.ycql_password,
            ysql_username=self.ysql_username,
            ysql_password=self.ysql_password,
            sslrootcert=self.sslrootcert)

    def populate_test_data(self, sqldbname, cqldbname, tbname, rowids, clean_data=True):
        """
        populate test data
        Args:
            sqldbname          (str)     --    sql database name
            cqldbname          (str)     --    cql keyspace name
            tbname             (str)     --    table name
            rowids             (list)    --    list of row ids
            clean_data       (boolean)   --    drop database and tables and recreate if True
        """
        if clean_data:
            self.__yugabytedb.drop_ysql_database(sqldbname)
            self.__yugabytedb.drop_ycql_database(cqldbname, tbname)
            self.__yugabytedb.create_ysql_database(sqldbname)
            self.__yugabytedb.create_ycql_database(cqldbname)
        self.__yugabytedb.create_ysql_table(sqldbname, tbname)
        self.__yugabytedb.create_ycql_table(cqldbname, tbname)
        self.__yugabytedb.add_ysql_data(sqldbname, tbname, rowids)
        self.__yugabytedb.add_ycql_data(cqldbname, tbname, rowids)

    def update_test_data(self, srcsqldbname, srccqldbname, tbname, rowids, deletedata=False):
        """
        update test data
        Args:
            srcsqldbname          (str)     --    sql database name
            srccqldbname          (str)     --    cql keyspace name
            tbname                (str)     --    table name
            rowids                (list)    --    list of row ids
            deletedata          (boolean)   --    delete  if True
        """
        self.__yugabytedb.update_ysql_data(srcsqldbname, tbname, rowids, deletedata)
        self.__yugabytedb.update_ycql_data(srccqldbname, tbname, rowids, deletedata)

    def add_credential(self):
        """add credential"""
        if not self._credentials_object.has_credential(self.credential_name):
            self._credentials_object.add_aws_s3_creds(
                credential_name=self.credential_name,
                access_key_id=self.aws_access_key,
                secret_access_key=self.aws_secret_key)
        self._credentials_object.refresh()
        if self._credentials_object.has_credential(self.credential_name):
            self.log.info("credential is created successfully")
        else:
            raise Exception("failed to add credential")

    def add_yugabyte_client(self):
        """
        Adds new yugabyte client by calling commcell object of cvpysdk

         Args:
             Nothing

        Returns:
            client  --  client object of the newly created yugabyte client

        """
        self.add_credential()
        if self.__commcell.clients.has_client(self.instance_name):
            self.log.info('Client exists. Deleting it and creating')
            self.__commcell.clients.delete(self.instance_name)

        self.client = self.__commcell.clients.add_yugabyte_client(
            self.instance_name, self.db_host, self.api_token, self.universe_name, self.config_name, self.credential_name,
            self.content, self.plan_name, self.data_access_nodes, self.user_uuid, self.universe_uuid, self.config_uuid)
        return self.client

    def get_client_details(self, client_object,
                           backupset_name="defaultbackupset",
                           subclient_name="default"):
        """
        Returns a dictionary containing client_obj, instance_obj,
        backupset_obj and agent_obj

        Args:
            client_object   (object)    --  yugabytedb client object

            backupset_name  (str)       --  name of the backupset entity
                default: defaultbackupset

            subclient_name  (str)       --  name of the subclient entity
                default: default

        Returns:
             client_details (dict)      --  dictionary containing client_obj, instance_obj,
             backupset_obj and agent_obj

        """

        req_agent = client_object.agents.get("big data apps")
        req_instance = req_agent.instances.get(client_object.client_name)
        req_backupset = req_agent.backupsets.get(backupset_name)
        req_subclient = req_backupset.subclients.get(subclient_name)
        req_subclient_id = req_subclient.subclient_id

        client_details = {
            "client": client_object,
            "agent": req_agent,
            "instance": req_instance,
            "backupset": req_backupset,
            "subclient": req_subclient,
            "subclient_id": req_subclient_id
        }

        return client_details

    def run_backup(self, client_object, client_details, subclient_details=None, backup_type="Full"):
        """
            Runs backup on the specified yugabytedb client object. Runs a Full backup by default

            Args:
                 client_object  (obj)   --  yugabytedb client object

                 subclient_details (obj)  --  Contains subclient_object
                                            Ex: Subclient class instance for Subclient: "default" of Backupset:
                                            "defaultbackupset"}

                backup_type(str)       --   Type of backup - Full/Incremental

            Return:
                  tuple: A tuple containing two elements:
                  - str: The job ID of the backup job.
        """

        self.log.info("Starting Backup Job")
        if subclient_details is None:
            req_agent = client_object.agents.get(self.agentname)
            req_backupset = req_agent.backupsets.get(self.backupsetname)
            req_subclient = req_backupset.subclients.get(self.subclientname)
        else:
            req_subclient = subclient_details
        job_obj = req_subclient.backup(backup_type)
        self.log.info("Waiting For Completion Of Backup Job With Job ID: %s",
                      str(job_obj.job_id))
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed To Run Backup {0} With Error {1}".format(
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
            "Successfully Finished Backup Job %s", str(job_obj.job_id)
        )

    def verify_restore(self, srcsqldbname, srccqldbname, destsqldbname, destcqldbname, tbname,
                       restoreoption=0):
        """
        verify restore with different options
        Args:
            srcsqldbname          (str)     --    sql database name
            srccqldbname          (str)     --    cql keyspace name
            destsqldbname         (str)     --    destination sql database name
            destcqldbname         (str)     --    destination cql database name
            tbname                (str)     --    table name
            restoreoption         (int)    :    0 - drop database and restore with same name
                                                1 - restore to new database from instance action
                                                2 - restore to new database from instance RPC
                                                3 - restore to new database from namespacegroup actions
                                                4 - drop db, new table and restore db from namespacegroup RPC
        """
        sql_origdata = self.__yugabytedb.get_ysql_rows(srcsqldbname, tbname)
        cql_origdata = self.__yugabytedb.get_ycql_rows(srccqldbname, tbname)
        if restoreoption == 0 and restoreoption == 2:
            self.__yugabytedb.drop_ysql_database(srcsqldbname)
            self.log.info("dropped keyspace %s", srcsqldbname)
            self.__yugabytedb.drop_ycql_database(srccqldbname, tbname)
            self.log.info("dropped keyspace %s", srccqldbname)
        else:
            self.__yugabytedb.drop_ysql_database(destsqldbname)
            self.log.info("dropped keyspace %s", destsqldbname)
            self.__yugabytedb.drop_ycql_database(destcqldbname, tbname)
            self.log.info("dropped keyspace %s", destcqldbname)
        self.run_restore(srcsqldbname, srccqldbname, destsqldbname, destcqldbname, tbname)
        self.log.info("restore successful. now validating data")
        time.sleep(60)
        self.validate_restoredata(sql_origdata, cql_origdata, destsqldbname, destcqldbname, tbname)

    def run_restore(self, srcsqldbname, srccqldbname, destsqldbname, destcqldbname, tbname,
                    wait_to_complete=True, instance_level_restore = True):
        """Restores database and verify the restored data
        Args:
            srcsqldbname          (str)     --    sql database name
            srccqldbname          (str)     --    cql keyspace name
            destsqldbname         (str)     --    destination sql database name
            destcqldbname         (str)     --    destination cql database name
            tbname                (str)     --    table name
            wait_to_complete      (bool)    --  Specifies whether to wait until restore job finishes.
            instance_level_restore(bool)    --    Specifies whether the restore is from instance or subclient level
        """
        self._agent_object = Agent(
            client_object=self.client,
            agent_name=self.agentname)
        self._instance_object = self._agent_object.instances.get(
            self.instance_name)
        client_details = self.get_client_details(self.client)
        db_paths = ["/"+srcsqldbname+".sql", "/"+srccqldbname+".cql"]
        restore_dict = {}
        restore_dict["no_of_streams"] = self.restore_no_of_stream
        restore_dict["multinode_restore"] = True
        restore_dict["destination_instance"] = self.instance_name
        restore_dict["destination_instance_id"] = self._instance_object.instance_id
        restore_dict["paths"] = db_paths
        restore_dict["destination_client_id"] = self.client.client_id
        restore_dict["destination_client_name"] = self.client.client_name
        restore_dict["client_type"] = 29
        restore_dict["destination_appTypeId"] = 64
        restore_dict["backupset_name"] = self.backupsetname

        if instance_level_restore:
            restore_dict["subclient_id"] = -1
            restore_dict["_type_"] = 5
        else:
            restore_dict["subclient_id"] = client_details.req_subclient_id
            restore_dict["_type_"] = 7

        restore_dict["sql_fromtable"] = srcsqldbname+'.sql'
        restore_dict["cql_fromtable"] = srccqldbname+'.cql'
        restore_dict["sql_totable"] = destsqldbname
        restore_dict["cql_totable"] = destcqldbname
        restore_dict["accessnodes"] = self.data_access_nodes
        restore_dict["kms_config"] = self.kms_config
        restore_dict["kmsconfigUUID"] = self.kmsconfig_uuid

        job_object = self._instance_object.restore(
            restore_options=restore_dict)
        self.log.info(
            "wait for restore job %s to complete",
            job_object._job_id)
        job_object.wait_for_completion(return_timeout=30)

    def validate_restoredata(self, srcsqldata, srccqldata, destsqldbname, destcqldbname, tbname):
        """"validate restore data in DB
        Args:
            srcsqldata            (str)     --    source sql data
            srccqldata            (str)     --    source cql data
            destsqldbname         (str)     --    destination sql database name
            destcqldbname         (str)     --    destination cql database name
            tbname                (str)     --    table name
        """
        self.log.info("inside validate method")
        print(srcsqldata, srccqldata)
        sql_destresult = self.__yugabytedb.get_ysql_rows(destsqldbname, tbname)
        cql_destresult = self.__yugabytedb.get_ycql_rows(destcqldbname, tbname)
        print(sql_destresult,cql_destresult)
        if srcsqldata == sql_destresult and srccqldata == cql_destresult:
            self.log.info("restored data match original data")
        else:
            raise Exception("Restored data doesn't match original data")

    def drop_db_and_restore(self, srcsqldbname, srccqldbname, tbname):
        """drop database and restore with same name from instance actions
        Args:
            srcsqldbname     (string)    - source sqldatabase name
            srccqldbname     (string)    - source sqldatabase name
            tbname           (string)    - table name
        """
        self.verify_restore(srcsqldbname,
                            srccqldbname,
                            srcsqldbname,
                            srccqldbname,
                            tbname=tbname,
                            restoreoption=0)

    def restore_to_newdb(self, srcsqldbname, srccqldbname, tbname):
        """restore to new database from instance actions
        Args:
            srcsqldbname     (string)    - source sqldatabase name
            srccqldbname     (string)    - source sqldatabase name
            tbname           (string)    - table name
        """
        self.drop_database(self.destsqldbname, self.destcqldbname, tbname)
        self.verify_restore(srcsqldbname,
                            srccqldbname,
                            self.destsqldbname,
                            self.destcqldbname,
                            tbname=tbname,
                            restoreoption=1)

    def new_table_restore(self, srcsqldbname, srccqldbname, tbname, tbname2):
        """new table restore from namespace group actions
        Args:
            srcsqldbname     (string)    - source sqldatabase name
            srccqldbname     (string)    - source sqldatabase name
            tbname           (string)    - table name
            tbname2          (string)    - new table name
        """
        self.drop_table(srcsqldbname, srccqldbname, tbname)
        self.verify_restore(srcsqldbname,
                            srccqldbname,
                            srcsqldbname,
                            srccqldbname,
                            tbname=tbname2,
                            restoreoption=2)

    def drop_database(self, sqldbname, cqldbname, tbname):
        """drop database
        Args:
            sqldbname     (string)    - source sqldatabase name to be dropped
            cqldbname     (string)    - source sqldatabase name to be dropped
            tbname           (string)    - table name to be dropped
        """
        self.__yugabytedb.drop_ycql_database(cqldbname, tbname)
        self.__yugabytedb.drop_ysql_database(sqldbname)

    def drop_table(self, sqldbname, cqldbname, tbname):
        """drop table
        Args:
            sqldbname     (string)    - source sqldatabase name to be dropped
            cqldbname     (string)    - source sqldatabase name to be dropped
            tbname           (string)    - table name to be dropped
        """
        self.__yugabytedb.drop_ycql_table(cqldbname, tbname)
        self.__yugabytedb.drop_ysql_table(sqldbname, tbname)

    def delete_yugabyte_client(self):
        """deletes the client"""
        if self.__commcell.clients.has_client(self.instance_name):
            self.log.info('Client exists. Deleting it')
            self.__commcell.clients.delete(self.instance_name)
        else :
            self.log.info('client does not exist')

    def close_dbconnection(self):
        """close yugabyteDB cluster connection"""
        self.__yugabytedb.close_connection()