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
    yugabyteDB:               Class for creating/deleting instances and running backup/restore
                                 for yugabyteDB instance Under Big data, It also has the methods to
                                 connect/disconnect to cql host, generate/modify/drop test data
                                 and validate restored data
        __init__()                                      --      constructor for creating yugabyteDB object
        refresh()                                       --      Refreshes the current page
        create_yugabytedb_instance()                    --      create yugabyteDB instance
        delete_yugabytedb_instance()                    --      delete yugabyteDB instance
        connect_to_db()                                 --      connect to yugabytedb cluster
        populate_test_data()                            --      populate test data
        update_test_data()                              --      update test data
        wait_for_job_completion()                       --      Waits until the job completes
        run_backup()                                    --      initiate backup job and verify backup job complete
        run_restore()                                   --      initiate restore job and verify restore job completed
        verify_restore()                                --      verify restore job and validate the restored data
        validate_restoredata()                          --      verified expected data are restored to yugabyteDB
                                                                cluster db
        backup_from_instance_action()                   --      initiate backup from instance actions
        backup_from_instance_overview()                 --      initiate backup from instance overview
        backup_from_namespacegroup_action()             --      initiate backupf rom namespace group actions
        drop_db_restore_from_instance_action()          --      drops database and restores with same db name from
                                                                instance actions
        restore_to_newdb_from_instance_action()         --      restores to a new database name from instance actions
        restore_to_newdb_from_instance_RPC()            --      restores to a new database name from instance RPC
        restore_to_newdb_from_namespacegroup_actions()  --      restores to a new database name from namaspace group
                                                                actions
        new_table_restore_from_namespacegroup_actions() --      restores new table from namespace group actions
        drop_database()                                 --      drops sql and cql test database
        drop_table()                                    --      drops sql and cql table
        close_dbconnection()                            --      shuts down yugabyteDB db connection
"""
#import psycopg
import time
import psycopg2
from Web.Common.page_object import TestStep
from Web.AdminConsole.Bigdata.instances import Instances, YugabyteDBServer
from Web.AdminConsole.Bigdata.details import Overview, NamespaceGroups
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.wizard import Wizard
from Web.Common.exceptions import CVTestStepFailure
from AutomationUtils import logger
from ssl import SSLContext, PROTOCOL_TLS_CLIENT, CERT_REQUIRED
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
class YugabyteDBHelper():
    """
        Helper class for YugabyteDB cluster related operations
    """
    def __init__(
            self,
            node_ip,
            ycql_username,
            ycql_password,
            ysql_username,
            ysql_password,
            sslrootcert):
        """
        Constructor for creating the yugabyteDB cluster connection
        Args:
                node_ip       (str)    -- yugabytedb cluster node ip
                ycql_username (str)    -- yugabytedb ycql username
                ycql_password (str)    -- yugabytedb ycql password
                ysql_username (str)    -- yugabytedb ysql username
                ysql_password (str)    -- yugabytedb ysql password
                sslrootcert (str)      -- path the ssl root cert on the controller. for eg : "C:\\certs\\ca.crt"
            Returns:
                object  -   connection object to the yugabyteDB cluster
            Raises:
                Exception:
                    if failed to connect to the database
        """
        self.node_ip = node_ip
        self.ycql_username = ycql_username
        self.ycql_password = ycql_password
        self.ysql_username = ysql_username
        self.ysql_password = ysql_password
        self.sslrootcert = sslrootcert
        self.log = logger.get_log()
        self._cluster = None
        self._connection = None
        self._cursor = None
        self._connect_to_ycqlsh()
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
                          auth_provider=PlainTextAuthProvider(username=self.ycql_username, password=self.ycql_password))
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
            cmd = "CREATE KEYSPACE IF NOT EXISTS " + cqldbname+";"
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
            print("dropped database %s",sqldbname)
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
    test_step = TestStep()
    def __init__(self, admin_console, testcase):
        """Constructor for creating the yugabyteDB object"""
        self._admin_console = admin_console
        self.__wizard = Wizard(admin_console)
        self.__instances = Instances(admin_console)
        self.__yugabytedb_server = YugabyteDBServer(self._admin_console)
        self.__overview = Overview(self._admin_console)
        self.__namespacegroups = NamespaceGroups(self._admin_console)
        self.__commcell = testcase.commcell
        self.__backup = Backup(admin_console)
        self.__yugabytedb = None
        self.yugabytedb_server_name = testcase.yugabytedb_server_name
        self.access_nodes = testcase.tcinputs.get("access_nodes")
        self.yugabytedb_host = testcase.tcinputs.get("yugabytedb_host")
        self.node_ip = testcase.tcinputs.get("node_ip")
        self.plan_name = testcase.tcinputs.get("plan_name")
        self.api_token = testcase.tcinputs.get("api_token")
        self.universe_name = testcase.tcinputs.get("universe_name")
        self.storage_config = testcase.tcinputs.get("storage_config")
        self.credential = testcase.tcinputs.get("credential")
        self.kms_config = testcase.tcinputs.get("kms_config")
        self.ysql_username = testcase.ysql_username
        self.ysql_password = testcase.ysql_password
        self.ycql_username = testcase.ycql_username
        self.ycql_password = testcase.ycql_password
        self.sslrootcert = testcase.sslrootcert
        self.sqldbname = testcase.sqldbname
        self.cqldbname = testcase.cqldbname
        self.destsqldbname = testcase.destsqldbname
        self.destcqldbname = testcase.destcqldbname
    def refresh(self, wait_time=30):
        """ Refreshes the current page """
        self._admin_console.log.info(
            "%s Refreshes browser %s", "*" * 8, "*" * 8)
        self._admin_console.refresh_page()
        time.sleep(wait_time)
    @test_step
    def create_yugabytedb_instance(self):
        """create yugabyteDB instance """
        self._admin_console.navigator.navigate_to_big_data()
        self.refresh()
        if self.__instances.is_instance_exists(self.yugabytedb_server_name):
            self.delete_yugabytedb_instance()
        _yugabytedb_server = self.__instances.add_yugabytedb_server()
        _yugabytedb_server.add_yugabytedb_parameters(self.access_nodes, self.plan_name,
                                                   self.yugabytedb_server_name, self.yugabytedb_host,
                                                   self.api_token, self.universe_name, self.storage_config,
                                                   self.credential, self.sqldbname, self.cqldbname)
        self._admin_console.navigator.navigate_to_big_data()
        self.refresh()
        if not self.__instances.is_instance_exists(self.yugabytedb_server_name):
            raise CVTestStepFailure(
                "[%s] yugabytedb instance is not getting created " %
                self.yugabytedb_server_name)
        self._admin_console.log.info(
            "Successfully Created [%s] yugabytedb instance",
            self.yugabytedb_server_name)
    @test_step
    def delete_yugabytedb_instance(self):
        """Delete yugabyteDB instance and verify instance is deleted"""
        self._admin_console.navigator.navigate_to_big_data()
        self.refresh()
        self.__instances.delete_instance_name(self.yugabytedb_server_name)
        if self.__instances.is_instance_exists(self.yugabytedb_server_name):
            raise CVTestStepFailure(
                "[%s] YugabyteDB instance is not getting deleted" %
                self.yugabytedb_server_name)
        self._admin_console.log.info(
            "Deleted [%s] instance successfully",
            self.yugabytedb_server_name)
    @test_step
    def connect_to_db(self):
        """initiate yugabytedb connection """
        self.__yugabytedb = YugabyteDBHelper(
            node_ip=self.node_ip,
            ycql_username=self.ycql_username,
            ycql_password=self.ycql_password,
            ysql_username=self.ysql_username,
            ysql_password=self.ysql_password,
            sslrootcert=self.sslrootcert)
    @test_step
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
    @test_step
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
    def wait_for_job_completion(self, job_id):
        """ Function to wait till job completes
                Args:
                    job_id (str): Entity which checks the job completion status
        """
        self._admin_console.log.info(
            "%s Waits for job completion %s", "*" * 8, "*" * 8)
        job_obj = self.__commcell.job_controller.get(job_id)
        return job_obj.wait_for_completion(timeout=300)
    def run_backup(self, backupoption=0, backuptype="INCREMENTAL"):
        """Initiate the backup and verify backup job is completed
        Args:
            backupoption        (int):   0 - run backup from instance actions
                                         1 - run backup from instance overview
                                         2 - run backup from namespacegroup action
            backuptype          (str):   backup type, "FULL" or "INCREMENTAL"
        """
        # Initiate backup job
        self._admin_console.navigator.navigate_to_big_data()
        self.refresh()
        if backupoption == 0:
            self.__instances.access_backup(self.yugabytedb_server_name)
        elif backupoption == 1:
            self.__instances.access_instance(self.yugabytedb_server_name)
            self._admin_console.click_button("Backup")
        else:
            self.__instances.access_instance(self.yugabytedb_server_name)
            self.__overview.access_namespacegroups()
            self.__namespacegroups.access_backup()
        self._admin_console.select_radio(id=backuptype)
        self._admin_console.click_button("Submit")
        _job_id = self._admin_console.get_jobid_from_popup()
        self.wait_for_job_completion(_job_id)
    def run_restore(
            self,
            kms_config,
            destinstance,
            dbtables,
            restoreoption=0):
        """ Initiate restore job
        Args:
            destinstance     (str)    :    destination instance name
            restoreoption    (int)    :    0 - drop database and restore with same name
                                           1 - restore to new database from instance action
                                           2 - restore to new database from instance RPC
                                           3 - restore to new database from namespacegroup actions
                                           4 - drop db, new table and restore db from namespacegroup RPC
            dbtables         (list)    :   list of databases to be restored
        """
        self._admin_console.navigator.navigate_to_big_data()
        self.refresh()
        if restoreoption == 0 & 1:
            self.__instances.access_restore(self.yugabytedb_server_name)
        elif restoreoption == 2:
            self.__instances.access_instance(self.yugabytedb_server_name)
            self._admin_console.click_button(id="submit-btn")
        elif restoreoption == 3:
            self.__instances.access_instance(self.yugabytedb_server_name)
            self.__overview.access_namespacegroups()
            self.__namespacegroups.access_restore("default")
        else:
            self.__instances.access_instance(self.yugabytedb_server_name)
            self.__overview.access_namespacegroups()
            self.__namespacegroups.access_namespacegroup("default")
            self._admin_console.click_button(id="submit-btn")
        _restore = self.__overview.select_restore_content(paths=dbtables)
        _restore.select_destination_instance(destinstance)
        _restore.set_kms_config(self.kms_config)
        _restore.set_destination_db_names(restoreoption)
        self._admin_console.click_button(id='Save')
        _job_id = self._admin_console.get_jobid_from_popup()
        self.wait_for_job_completion(_job_id)
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
        if restoreoption == 0 & restoreoption == 4:
            self.__yugabytedb.drop_ysql_database(srcsqldbname)
            self._admin_console.log.info("dropped keyspace %s", srcsqldbname)
            self.__yugabytedb.drop_ycql_database(srccqldbname, tbname)
            self._admin_console.log.info("dropped keyspace %s", srccqldbname)
        else:
            self.__yugabytedb.drop_ysql_database(destsqldbname)
            self._admin_console.log.info("dropped keyspace %s", destsqldbname)
            self.__yugabytedb.drop_ycql_database(destcqldbname, tbname)
            self._admin_console.log.info("dropped keyspace %s", destcqldbname)
        self.run_restore(self.kms_config, destinstance=self.yugabytedb_server_name,
                             dbtables=[srcsqldbname, srccqldbname],
                             restoreoption=restoreoption)
        self.validate_restoredata(sql_origdata, cql_origdata, destsqldbname, destcqldbname, tbname)
    def validate_restoredata(self, srcsqldata, srccqldata, destsqldbname, destcqldbname, tbname):
        """"validate restore data in DB
        Args:
            srcsqldata            (str)     --    source sql data
            srccqldata            (str)     --    source cql data
            destsqldbname         (str)     --    destination sql database name
            destcqldbname         (str)     --    destination cql database name
            tbname                (str)     --    table name
        """
        sql_destresult = self.__yugabytedb.get_ysql_rows(destsqldbname, tbname)
        cql_destresult = self.__yugabytedb.get_ycql_rows(destcqldbname, tbname)
        if srcsqldata == sql_destresult and srccqldata == cql_destresult:
            self._admin_console.log.info("restored data match original data")
        else:
            raise CVTestStepFailure(
                "restored data does not match original data")
    @test_step
    def backup_from_instance_action(self, backuptype="INCREMENTAL"):
        """run backup job from instance actions
        Args:
            backuptype     (str)    -- backup job type,  FULL or INCREMENTAL
        """
        self.run_backup(0, backuptype)
    @test_step
    def backup_from_instance_overview(self, backuptype="INCREMENTAL"):
        """run backup job from instance overview page
        Args:
            backuptype     (str)    -- backup job type,  FULL or INCREMENTAL
        """
        self.run_backup(1, backuptype)
    @test_step
    def backup_from_namespacegroup_action(self, backuptype="INCREMENTAL"):
        """run backup job from namespacegroup actions page
        Args:
            backuptype     (str)    -- backup job type,  FULL or INCREMENTAL
        """
        self.run_backup(2, backuptype)
    @test_step
    def drop_db_restore_from_instance_action(self, srcsqldbname, srccqldbname, tbname):
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
    @test_step
    def restore_to_newdb_from_instance_action(self, srcsqldbname, srccqldbname, tbname):
        """restore to new database from instance actions
        Args:
            srcsqldbname     (string)    - source sqldatabase name
            srccqldbname     (string)    - source sqldatabase name
            tbname           (string)    - table name
        """
        self.drop_database(self.destsqldbname,self.destcqldbname,tbname)
        self.verify_restore(srcsqldbname,
                            srccqldbname,
                            self.destsqldbname,
                            self.destcqldbname,
                            tbname=tbname,
                            restoreoption=1)
    @test_step
    def restore_to_newdb_from_instance_RPC(self, srcsqldbname, srccqldbname, tbname):
        """restore to new database from instance details Recovery point calendar
        Args:
            srcsqldbname     (string)    - source sqldatabase name
            srccqldbname     (string)    - source sqldatabase name
            tbname           (string)    - table name
        """
        self.verify_restore(srcsqldbname,
                            srccqldbname,
                            self.destsqldbname,
                            self.destcqldbname,
                            tbname=tbname,
                            restoreoption=2)
    @test_step
    def restore_to_newdb_from_namespacegroup_actions(self, srcsqldbname, srccqldbname, tbname):
        """restore to new database from namespacegroup actions
        Args:
            srcsqldbname     (string)    - source sqldatabase name
            srccqldbname     (string)    - source sqldatabase name
            tbname           (string)    - table name
        """
        self.verify_restore(srcsqldbname,
                            srccqldbname,
                            self.destsqldbname,
                            self.destcqldbname,
                            tbname=tbname,
                            restoreoption=3)
    @test_step
    def new_table_restore_from_namespacegroup_actions(self, srcsqldbname, srccqldbname, tbname, tbname2):
        """new table restore from namespace group actions
        Args:
            srcsqldbname     (string)    - source sqldatabase name
            srccqldbname     (string)    - source sqldatabase name
            tbname           (string)    - table name
            tbname2          (string)    - new table name
        """
        self.drop_table(srcsqldbname, srccqldbname, tbname)
        #self.drop_table(srcsqldbname, srccqldbname, tbname2)
        self.verify_restore(srcsqldbname,
                            srccqldbname,
                            srcsqldbname,
                            srccqldbname,
                            tbname=tbname2,
                            restoreoption=4)
    @test_step
    def drop_database(self, sqldbname, cqldbname, tbname):
        """drop database
        Args:
            sqldbname     (string)    - source sqldatabase name to be dropped
            cqldbname     (string)    - source sqldatabase name to be dropped
            tbname           (string)    - table name to be dropped
        """
        self.__yugabytedb.drop_ycql_database(cqldbname, tbname)
        self.__yugabytedb.drop_ysql_database(sqldbname)
    @test_step
    def drop_table(self, sqldbname, cqldbname, tbname):
        """drop table
        Args:
            sqldbname     (string)    - source sqldatabase name to be dropped
            cqldbname     (string)    - source sqldatabase name to be dropped
            tbname           (string)    - table name to be dropped
        """
        self.__yugabytedb.drop_ycql_table(cqldbname, tbname)
        self.__yugabytedb.drop_ysql_table(sqldbname, tbname)
    @test_step
    def close_dbconnection(self):
        """close yugabyteDB cluster connection"""
        self.__yugabytedb.close_connection()
