# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""

Helper file for cassandra cluster related operations.

Classes defined in this file:

    CassandraHelper:         Class for connecting to cql host and performing cqlsh queries.

        __init__()                 --  Constructor for creating a connection to Cassandra cluster

        _getnodeip()               --  return list of cql host ips/names

        _connect()                 --  create cluster object and initiate the connection

        connection()               --  return the cassandra cluster connection object

        createkeyspace()           --  execute cql query to create a test keyspace

        dropkeyspace()             --  execute cql query to drop the test keyspace

        createtable()              --  create table

        droptable()                --  drop table

        truncatetable()            --  truncate table

        check_if_keyspace_exists() --  check if the specified keyspace exist

        check_if_table_exists()    --  check if the specified table exist

        get_rows()                 --  get the rows in the table

        populate_test_data         --  insert test data into the specified table

        close_connection()         --  shutdown the db connection


    Cassandra:               Class for creating/deleting instances and running backup/restore
                                 for cassandra instance Under Big data, It also has the methods to
                                 connect/disconnect to cql host, generate/modify/drop test data
                                 and validate restored data

        __init__()                  --  constructor for creating cassandra object

        create_cassandra_instance() --  create cassandra pesudo client

        verify_backup()             --  run backup job and verify backup job complete

        verify_log_backup()         --  run log backup and verify log backup job is complete

        enable_commitlogs()         --  enable and configure commit log properties

        edit_node()                 --  edits cassandra nodes

        verify_restore()            --  run restore job and verify restore job complete

        delete_cassandra_instance() --  delete cassandra instance and pseudo client

        generate-test_data()        --  generate test data

        drop_keyspace()             --  drop keysapce

        drop_table()                --  drop table

        truncate_table()            --  truncate table

        validate_restore()          --  verified expected data are restored to cassandra cluster db

        close_dbconnection()        --  shutdown cassandra db connection
"""
import time
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, ExecutionProfile
from ssl import SSLContext

from Web.Common.page_object import TestStep
from Web.AdminConsole.Bigdata.instances import Instances, CassandraServer
from Web.AdminConsole.Bigdata.details import Overview, DataCenter
from Web.Common.exceptions import CVTestStepFailure
from AutomationUtils import logger


class CassandraHelper():
    """
        Helper class for Cassandra cluster related operations
    """

    def __init__(
            self,
            cql_host,
            cql_username,
            cql_password,
            cql_port,
            ssl_enabled=False):
        """
        Constructor for creating the cassandra cluster connection
        Args:
                cql_host (str)        -- cql host name or ip

                cql_username (str)    -- cql username

                cql_password (str)    -- cql user password

            Returns:
                object  -   connection object to the cassandra cluster

            Raises:
                Exception:
                    if failed to connect to the database

        """
        self.cql_host = cql_host
        self.cql_username = cql_username
        self.cql_password = cql_password
        self.cql_port = int(cql_port)
        self.log = logger.get_log()
        self._cluster = None
        self._connection = None
        self._connect(ssl_enabled)

    def _getnodeip(self):
        """return list of cql host ips"""
        node_ips = [self.cql_host]
        return node_ips

    @property
    def connection(self):
        """return cassandra cluster connection object"""
        return self._connection

    def _connect(self, ssl_enabled):
        """initiation Cluster object and connect to cassandra cql host """
        try:
            auth_provider = PlainTextAuthProvider(
                username=self.cql_username,
                password=self.cql_password)
            execution_profil = ExecutionProfile(request_timeout=180)
            profiles = {'node1': execution_profil}
            if ssl_enabled:
                ssl_context = SSLContext()
                self._cluster = Cluster(
                    self._getnodeip(),
                    auth_provider=auth_provider,
                    port=self.cql_port,
                    ssl_context=ssl_context,
                    execution_profiles=profiles)
            else:
                self._cluster = Cluster(
                    self._getnodeip(),
                    auth_provider=auth_provider,
                    port=self.cql_port,
                    execution_profiles=profiles)
            self._connection = self._cluster.connect()
            self.log.info("cassandra cluster connection is create")
        except Exception as excp:
            raise Exception(
                'Failed to connect to cassandra server\nERror: "{0}"'.format(excp))

    def createkeyspace(self, keyspace):
        """
        create keyspace
        Args:
                keyspace (str)        -- new keyspace name

            Raises:
                Exception:
                    if failed to create keyspace
        """
        try:
            cmd = "CREATE KEYSPACE IF NOT EXISTS " + keyspace + \
                " WITH replication = {'class': 'SimpleStrategy', \
                'replication_factor': '1'}  AND durable_writes = true;"
            self._connection.execute(cmd, execution_profile='node1')
            self.log.info("keyspce created")
        except Exception:
            raise Exception("unable to create keyspace")

    def dropkeyspace(self, keyspace):
        """
        drop keyspace
        Args:
                keyspace (str)        -- new keyspace name

            Raises:
                Exception:
                    if failed to drop keyspace
        """
        try:
            cmd = "drop keyspace " + keyspace
            self._connection.execute(cmd, execution_profile='node1')
            self.log.info("keyspace dropped")
        except Exception:
            raise Exception("Unable to drop keyspace")

    def createtable(self, keyspace, tablename):
        """
        create table in keyspace
        Args:
                keyspace (str)        -- keyspace name
                tablename (str)       -- new table name

            Raises:
                Exception:
                    if failed to create table
        """
        try:
            cmd = "CREATE TABLE IF NOT EXISTS " + keyspace + "." + \
                tablename + " ( id int PRIMARY KEY, fname text, lname text)"
            self._connection.execute(cmd, execution_profile='node1')
            self.log.info("table created")
        except Exception:
            raise Exception("unable to create table")

    def droptable(self, keyspace, table):
        """
        drop table from keyspace
        Args:
                keyspace (str)        -- keyspace name
                table (str)       -- table name

            Raises:
                Exception:
                    if failed to drop table
        """
        try:
            cmd = "drop table " + keyspace + "." + table
            self._connection.execute(cmd, execution_profile='node1')
            self.log.info("table dropped")
        except Exception:
            raise Exception("unable to drop table")

    def truncatetable(self, keyspace, table):
        """
        truncate table in keyspace
        Args:
                keyspace (str)        -- keyspace name
                tablename (str)       -- new table name

            Raises:
                Exception:
                    if failed to truncate table
        """
        try:
            cmd = "truncate table " + keyspace + "." + table
            self._connection.execute(cmd, execution_profile='node1')
            self.log.info("table truncated")
        except Exception:
            raise Exception("failed to truncate table")

    def check_if_keyspace_exists(self, keyspace):
        """
        check if keyspace exist
        Args:
                keyspace (str)        -- keyspace name
            Return:
                True if keyspace exist
        """
        keyspaces = self._connection.execute(
            'select keyspace_name from system_schema.keyspaces',
            execution_profile='node1')
        if keyspace not in keyspaces:
            return False
        return True

    def check_if_table_exists(self, keyspace, table):
        """
        check if table exist
        Args:
                keyspace (str)        -- keyspace name
                table (str)         -- table name
            Return:
                True if table exist
        """
        cmd = "select table_name from system_schema.tables where keyspace_name=" + keyspace
        tables = self._connection.execute(cmd, execution_profile='node1')
        if table not in tables:
            return False
        return True

    def get_rows(self, keyspace, table):
        """
        get rows ResultSet from table under keyspace
        Args:
                keyspace (str)        -- keyspace name
                table (str)         -- table name
            Return:
                ResultSets for rows in table
        """
        try:
            cmd = "select * from " + keyspace + "." + table
            rows = self._connection.execute(cmd, execution_profile='node1')
            return rows
        except Exception:
            raise Exception("failed to get table rows")

    def populate_test_data(self, keyspace, table, rows):
        """
        populate test data
        Args:
                keyspace (str)        -- keyspace name
                table (str)         -- table name
            Raises:
                Exceptions if populating test data failed
        """
        try:
            cmd1 = "insert into " + keyspace + "." + \
                table + "(id, fname, lname) values("
            cmd2 = ", 'test', 'test')"
            for row in rows:
                cmd = cmd1 + str(row) + cmd2
                self._connection.execute(cmd, execution_profile='node1')
            self.log.info("test data populated")
        except Exception:
            raise Exception("failed to populate test data")

    def close_connection(self):
        """close the connection to cassandra cluster"""
        if self.connection is not None:
            self._connection.shutdown()
            self._connection = None


class Cassandra:
    """
    class has the functions to operate Cassandra instances Under Big data Apps
    """
    test_step = TestStep()

    def __init__(self, admin_console, testcase):
        """Constructor for creating the cassandra object"""
        self._admin_console = admin_console
        self.__instances = Instances(admin_console)
        self.__cassandra_server = CassandraServer(self._admin_console)
        self.__overview = Overview(self._admin_console)
        self.__datacenter = DataCenter(self._admin_console)
        self.__commcell = testcase.commcell
        self.__cassandra = None
        self.cassandra_server_name = testcase.cassandra_server_name
        self.gatewaynode = testcase.tcinputs.get("gateway_node")
        self.config_file_path = testcase.tcinputs.get("config_file_path")
        self.cql_host = testcase.tcinputs.get("cql_host")
        self.plan_name = testcase.tcinputs.get("plan")
        self.cql_username = testcase.cql_username
        self.cql_password = testcase.cql_password
        self.cql_port = testcase.tcinputs.get("cql_port")
        self.jmx_port = testcase.tcinputs.get("jmx_port")
        self.jmx_username = testcase.jmx_username
        self.jmx_password = testcase.jmx_password
        self.archive_path = testcase.tcinputs.get("archive_path")
        self.archive_command = testcase.tcinputs.get("archive_command")
        self.keystore = testcase.ssl_keystore
        self.keystorepwd = testcase.ssl_keystorepwd
        self.truststore = testcase.ssl_truststore
        self.truststorepwd = testcase.ssl_truststorepwd
        self.staging_path = testcase.tcinputs.get("staging_path")
        self.configpath = testcase.tcinputs.get("configpath")
        self.datapath = testcase.tcinputs.get("datapath")
        self.javapath = testcase.tcinputs.get("javapath")

    def set_instanceparameter(self):
        """
        Creates a dictionary for test case inputs needed for customer package install.
        """
        inputs = {}
        try:
            inputs["clustername"] = self.cassandra_server_name
            inputs["node"] = self.gatewaynode
            inputs["planname"] = self.plan_name
            inputs["cqlusername"] = self.cql_username
            inputs["cqlpassword"] = self.cql_password
            inputs["cqlport"] = self.cql_port
            inputs["jmxport"] = self.jmx_port
            inputs["jmxusername"] = self.jmx_username
            inputs["jmxpassword"] = self.jmx_password
            inputs["keystore"] = self.keystore
            inputs["keystorepassword"] = self.keystorepwd
            inputs["truststore"] = self.truststore
            inputs["truststorepassword"] = self.truststorepwd
            inputs["configfilepath"] = self.config_file_path
            return inputs
        except BaseException:
            raise Exception("failed to set inputs for interactive install")

    @test_step
    def create_cassandra_instance(self, ssl=False, jmx=True, cql=True):
        """create cassandra instance """
        self._admin_console.navigator.navigate_to_big_data()
        if self.__instances.is_instance_exists(self.cassandra_server_name):
            self.delete_cassandra_instance()
        _cassandra_server = self.__instances.add_cassandra_server()
        _instanceparam = self.set_instanceparameter()
        _cassandra_server.add_cassandra_server(_instanceparam, ssl, jmx, cql)

        self._admin_console.navigator.navigate_to_big_data()
        self.refresh()
        if not self.__instances.is_instance_exists(self.cassandra_server_name):
            raise CVTestStepFailure(
                "[%s] Cassandra server is not getting created " %
                self.cassandra_server_name)
        self._admin_console.log.info(
            "Successfully Created [%s] cassandra server instance",
            self.cassandra_server_name)

    def wait_for_job_completion(self, job_id):
        """ Function to wait till job completes
                Args:
                    job_id (str): Entity which checks the job completion status
        """
        self._admin_console.log.info(
            "%s Waits for job completion %s", "*" * 8, "*" * 8)
        job_obj = self.__commcell.job_controller.get(job_id)
        return job_obj.wait_for_completion(timeout=300)

    def refresh(self, wait_time=30):
        """ Refreshes the current page """
        self._admin_console.log.info(
            "%s Refreshes browser %s", "*" * 8, "*" * 8)
        self._admin_console.refresh_page()
        time.sleep(wait_time)

    @test_step
    def verify_backup(self):
        """Initiate the backup and verify backup job is completed"""
        # Initiate backup job
        self.refresh()
        self._admin_console.navigator.navigate_to_big_data()
        self.__instances.access_instance(self.cassandra_server_name)
        self.__overview.access_datacenter()
        _job_id = self.__datacenter.backup()
        self.wait_for_job_completion(_job_id)

    @test_step
    def verify_log_backup(self):
        """Initiate the backup and verify log backup job is completed"""
        # Initiate backup job
        self._admin_console.navigator.navigate_to_big_data()
        self.__instances.access_instance(self.cassandra_server_name)
        self.__overview.access_datacenter()
        _job_id = self.__datacenter.backup_log()
        self.wait_for_job_completion(_job_id)

    @test_step
    def enable_commitlogs(self):
        """enables commitlogs toggle and configures archive path and archive command"""
        self._admin_console.navigator.navigate_to_big_data()
        self.__instances.access_instance(self.cassandra_server_name)
        config = self.__overview.access_configuration()
        config.set_archive_properties(self.archive_path, self.archive_command)

    @test_step
    def discover_node(self):
        """discover cassandra node"""
        self._admin_console.navigator.navigate_to_big_data()
        self.__instances.access_instance(self.cassandra_server_name)
        nodes = self.__overview.access_nodes()
        nodes.discover_nodes()

    @test_step
    def edit_node(self):
        """edit cassandra nodes"""
        self._admin_console.navigator.navigate_to_big_data()
        self.__instances.access_instance(self.cassandra_server_name)
        config = self.__overview.access_configuration()
        config.edit_cassandra_node(
            self.configpath, self.datapath, self.javapath)

    @test_step
    def verify_restore(
            self,
            paths,
            destinstance,
            stagefree=True,
            sstableloader=True,
            clusterview=False,
            restorelogs=False):
        """Initiate restore and verify restore job complete"""
        self.refresh()
        self._admin_console.navigator.navigate_to_big_data()
        self.__instances.access_instance(self.cassandra_server_name)
        self.__overview.access_datacenter()
        self.__datacenter.access_restore()
        self._admin_console.wait_for_completion()

        if clusterview:
            _restore = self.__overview.select_restore_content(
                paths=paths, view="Cluster view")
        else:
            _restore = self.__overview.select_restore_content(
                paths=paths, view="Keyspace view")

        _restore.select_destination_instance(destination_instance=destinstance)

        if sstableloader:
            _restore.use_sstableloader_tool()
            _restore.set_staging_location(self.staging_path)
            if stagefree:
                _restore.select_stage_free_restore()

        if not restorelogs:
            _restore.deselect_restore_logs()

        _restore.click_restore_and_confirm()
        _job_id = self._admin_console.get_jobid_from_popup()
        self.wait_for_job_completion(_job_id)

    @test_step
    def drop_keyspace_inplacerestore(
            self,
            paths,
            destinstance,
            keyspace,
            tablename,
            rows):
        """drop keyspace, DB veiw in place restore w/o sstableloader, validate restored data"""
        self.drop_keyspace(keyspace)
        self.verify_restore(
            paths=paths,
            destinstance=destinstance,
            stagefree=False,
            sstableloader=False)
        self.validate_restoredata(keyspace, tablename, rows)

    @test_step
    def drop_keyspace_inplacerestore_sstableloader(
            self, paths, destinstance, keyspace, tablename, rows):
        """drop keyspace, DB view in place restore w/ sstableloaer, validate restored data"""
        self.drop_keyspace(keyspace)
        self.verify_restore(
            paths=paths,
            destinstance=destinstance,
            stagefree=False)
        self.validate_restoredata(keyspace, tablename, rows)

    @test_step
    def drop_table_inplacerestore(
            self,
            paths,
            destinstance,
            keyspace,
            tablename,
            rows):
        """drop table, DB view in place restore w/o sstableloader, validate restored data"""
        self.drop_table(keyspace, tablename)
        self.verify_restore(
            paths=paths,
            destinstance=destinstance,
            stagefree=False,
            sstableloader=False)
        self.validate_restoredata(keyspace, tablename, rows)

    @test_step
    def drop_table_inplacerestore_sstableloader(
            self, paths, destinstance, keyspace, tablename, rows):
        """drop table, DB view in place restore w/ sstableloader, validate restored data"""
        self.drop_table(keyspace, tablename)
        self.verify_restore(
            paths=paths,
            destinstance=destinstance,
            stagefree=False)
        self.validate_restoredata(keyspace, tablename, rows)

    @test_step
    def drop_keyspace_clusterview_inplacerestore(
            self, paths, destinstance, keyspace, tablename, rows):
        """drop keyspace, Cluster veiw in place restore w/o sstableloader, validate restored data"""
        self.drop_keyspace(keyspace)
        self.verify_restore(paths=paths,
                            destinstance=destinstance,
                            stagefree=False,
                            sstableloader=False,
                            clusterview=True,)
        self.validate_restoredata(keyspace, tablename, rows)

    @test_step
    def drop_keyspace_clusterview_inplacerestore_sstableloader(
            self, paths, destinstance, keyspace, tablename, rows):
        """drop keyspace, cluster view in place restore w/ sstableloaer, validate restored data"""
        self.drop_keyspace(keyspace)
        self.verify_restore(
            paths=paths,
            destinstance=destinstance,
            stagefree=False,
            clusterview=True)
        self.validate_restoredata(keyspace, tablename, rows)

    @test_step
    def drop_table_clusterview_inplacerestore(
            self, paths, destinstance, keyspace, tablename, rows):
        """drop table, cluster view in place restore w/o sstableloader,validate restored data"""
        self.drop_table(keyspace, tablename)
        self.verify_restore(
            paths=paths,
            destinstance=destinstance,
            stagefree=False,
            sstableloader=False,
            clusterview=True)
        self.validate_restoredata(keyspace, tablename, rows)

    @test_step
    def drop_table_clusterview_inplacerestore_sstableloader(
            self, paths, destinstance, keyspace, tablename, rows):
        """drop table, cluster view, in place restore with sstableloader, validate restored data """
        self.drop_table(keyspace, tablename)
        self.verify_restore(
            paths=paths,
            destinstance=destinstance,
            stagefree=False,
            clusterview=True)
        self.validate_restoredata(keyspace, tablename, rows)

    @test_step
    def delete_cassandra_instance(self):
        """Delete cassandra instance and verify instance is deleted"""
        self._admin_console.navigator.navigate_to_big_data()
        self.__instances.delete_instance_name(self.cassandra_server_name)
        if self.__instances.is_instance_exists(self.cassandra_server_name):
            raise CVTestStepFailure(
                "[%s] Cassandra server is not getting deleted" %
                self.cassandra_server_name)
        self._admin_console.log.info(
            "Deleted [%s] instance successfully",
            self.cassandra_server_name)

    @test_step
    def connect_to_db(self, ssl_enabled=False):
        """initiate connection to cassandra cql host"""
        self.__cassandra = CassandraHelper(self.cql_host,
                                           self.cql_username,
                                           self.cql_password,
                                           self.cql_port,
                                           ssl_enabled=ssl_enabled)

    @test_step
    def generate_test_data(self, keyspace, tablename, rows, clean_data=True):
        """generate test data"""
        if clean_data:
            try:
                self.drop_keyspace(keyspace)
            except BaseException:
                pass
            self.__cassandra.createkeyspace(keyspace)
            self.__cassandra.createtable(keyspace, tablename)
        self.__cassandra.populate_test_data(keyspace, tablename, rows)

    @test_step
    def drop_keyspace(self, keyspace):
        """drop keyspace"""
        self.__cassandra.dropkeyspace(keyspace)

    @test_step
    def drop_table(self, keyspace, table):
        """drop table"""
        self.__cassandra.droptable(keyspace, table)

    @test_step
    def truncate_table(self, keyspace, table):
        """truncate table"""
        self.__cassandra.truncatetable(keyspace, table)

    @test_step
    def validate_restoredata(self, keyspace, table, rows):
        """"validate restore data in DB"""
        results = self.__cassandra.get_rows(keyspace, table)
        count = 0
        for result in results:
            count += 1
            if (result.id not in rows) or (
                    result.fname != 'test') or (result.lname != 'test'):
                raise CVTestStepFailure(
                    "restored data does not match with original data")
        if count == len(rows):
            self._admin_console.log.info("restored data match original data")
        else:
            raise CVTestStepFailure(
                "number of rows in restored data does not match original data")

    @test_step
    def close_dbconnection(self):
        """close cassandra cluster connection"""
        self.__cassandra.close_connection()
