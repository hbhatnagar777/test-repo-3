# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""

Helper file for cockroachDB cluster related operations.

Classes defined in this file:

    cockroachDBHelper:         Class for connecting to cockroachDB cluster and performing db queries.

        __init__()                 --  Constructor for creating a connection to cockroachDB cluster

        _connect()                 --  create cluster object and initiate the connection

        connection()               --  return the cockroachDB cluster connection object

        create_database()           --  execute db query to create a test database

        drop_database()             --  execute db query to drop the test dabase

        create_table()              --  execute db query to create table

        drop_table()                --  eecute db query to drop table

        add_data()                --    add test data

        truncate_table()            --  truncate table

        update_data()            --  update test data

        refresh_connection()    --  refresh db connection

        get_rows()                 --  get the rows resultsets from table

        close_connection()         --  close the db connection


    cockroachDB:               Class for creating/deleting instances and running backup/restore
                                 for cockroachDB instance Under Big data, It also has the methods to
                                 connect/disconnect to cql host, generate/modify/drop test data
                                 and validate restored data

        __init__()                  --  constructor for creating cockroachDB object

        set_instnaceparameters()    --    create dictionary for cockroachdb cluster parameter

        create_cockroachdb_instance() --  create cockroachDB instance

        delete_cockroachdb_instance()    -- delete cockroachDB instance

        connect_to_db()            --    connect to cockroachdb cluster

        populate_test_data()       --    populate test data

        update_test_data()        --    update test data

        run_backup()              --    initiate backup job and verify backup job complete

        run_restore()             --    initiate restore job and verify restore job completed

        verify_restore()          --    verify restore job and validate the restored data

        validate_restoredata()     --  verified expected data are restored to cockroachDB cluster db

        drop_database()            --    drop test database

        close_dbconnection()        --  shutdown cockroachDB db connection
"""
import psycopg
import time

from Web.Common.page_object import TestStep
from Web.AdminConsole.Bigdata.instances import Instances, CockroachDBServer
from Web.AdminConsole.Bigdata.details import Overview, TableGroups
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.wizard import Wizard
from Web.Common.exceptions import CVTestStepFailure
from AutomationUtils import logger


class CockroachDBHelper():
    """
        Helper class for CockroachDB cluster related operations
    """

    def __init__(
            self,
            db_host,
            db_username,
            db_password,
            db_port,
            ssl_enabled=True,
            sslrootcert=None,
            sslcert=None,
            sslkey=None):
        """
        Constructor for creating the cockroachDB cluster connection
        Args:
                db_host (str)        -- cockroachdb host name or ip

                db_username (str)    -- cockroachdb username

                db_password (str)    -- cockroachdb user password

                db_port    (int)     -- cockroachdb port number

                ssl_enabled (boolean)-- ssl is enabled if True

                sslrootcert (str)    --    path the ssl root cert

                sslcert     (str)    --    path for ssl client cert

                sslkey      (str)    --    path for ssl client key

            Returns:
                object  -   connection object to the cockroachDB cluster

            Raises:
                Exception:
                    if failed to connect to the database

        """
        self.cockroachdb_host = db_host
        self.cockroachdb_username = db_username
        self.cockroachdb_password = db_password
        self.cockroachdb_port = int(db_port)
        self.sslrootcert_on_ctrl = sslrootcert
        self.sslcert_on_ctrl = sslcert
        self.sslkey_on_ctrl = sslkey
        self.log = logger.get_log()
        self._cluster = None
        self._connection = None
        self._cursor = None
        self._connect(ssl_enabled)
        self.sslenabled = ssl_enabled

    @property
    def connection(self):
        """return cockroachDB cluster connection object"""
        return self._connection

    def _connect(self, ssl_enabled):
        """initiation Cluster object and connect to cockroachDB cluster """
        try:
            if ssl_enabled:
                self._connection = psycopg.connect(
                    host=self.cockroachdb_host,
                    port=self.cockroachdb_port,
                    dbname="defaultdb",
                    user=self.cockroachdb_username,
                    password=self.cockroachdb_password,
                    sslmode="verify-full",
                    sslrootcert=self.sslrootcert_on_ctrl,
                    sslcert=self.sslcert_on_ctrl,
                    sslkey=self.sslkey_on_ctrl)
            else:
                self._connection = psycopg.connect(
                    host=self.cockroachdb_host,
                    port=self.cockroachdb_port,
                    dbname="defaultdb",
                    user=self.cockroachdb_username,
                    password=self.cockroachdb_password,
                    sslmode="disable")
            self._cursor = self._connection.cursor()
            self.log.info("cockroachdb cluster connection created")
        except Exception as excp:
            raise Exception(
                'Failed to connect to cockroachdb cluster\nERror: "{0}"'.format(excp))

    def create_database(self, dbname):
        """
        create database
        Args:
            dbname (str)        -- database name to be created
        """
        with self._connection.cursor() as curs:
            cmd = "CREATE DATABASE IF NOT EXISTS " + dbname
            curs.execute(cmd)
            self._connection.commit()
            self.log.info(
                "create_database: status message: %s",
                curs.statusmessage)

    def drop_database(self, dbname):
        """
        drop database
        Args:
            dbname (str)        -- database name to be dropped
        """
        with self._connection.cursor() as curs:
            cmd = "DROP DATABASE IF EXISTS " + dbname + " CASCADE"
            curs.execute(cmd)
            self._connection.commit()
            self.log.info(
                "drop_database: status message: %s",
                curs.statusmessage)

    def create_table(self, dbname, tbname):
        """
        create table
        Args:
            dbname (str)        -- database name
            tbname (str)        -- table name to be created
        """
        with self._connection.cursor() as curs:
            cmd = "CREATE TABLE IF NOT EXISTS " + dbname + "." + \
                tbname + "(id INT PRIMARY KEY, lname STRING, fname STRING)"
            curs.execute(cmd)
            self._connection.commit()
            self.log.info(
                "create_table: status message: %s",
                curs.statusmessage)

    def drop_table(self, dbname, tbname):
        """
        drop table
        Args:
            dbname (str)        -- database name
            tbname (str)        -- table name to be dropped
        """
        with self._connection.cursor() as curs:
            cmd = "DROP TABLE IF EXISTS " + dbname + "." + tbname
            curs.execute(cmd)
            self._connection.commit()
            self.log.info("drop_table: status message: %s", curs.statusmessage)

    def add_data(self, dbname, tbname, ids):
        """
        add data into tables
        Args:
            dbname (str)        -- database name
            tbname (str)        -- table name
            ids    (list)      -- list of row ids
        """
        with self._connection.cursor() as curs:
            for testid in ids:
                cmd = "insert into " + dbname + "." + tbname + \
                    "(id, fname, lname) values(" + str(testid) + ", 'fname', 'lname')"
                curs.execute(cmd)
                self.log.info(
                    "insert_data: id: %s, status message: %s",
                    testid,
                    curs.statusmessage)
            self._connection.commit()

    def truncate_table(self, dbname, tbname):
        """
        truncate tables
        Args:
            dbname (str)        -- database name
            tbname (str)        -- table name
        """
        with self._connection.cursor() as curs:
            cmd = "TRUNCATE " + dbname + "." + tbname
            curs.execute(cmd)
            self._connection.commit()
            self.log.info(
                "truncate_table: status message: %s",
                curs.statusmessage)

    def update_data(self, dbname, tbname, ids, deletedata=False):
        """
        update test data
        Args:
            dbname (str)        -- database name
            tbname (str)        -- table name
            ids    (list)          -- list of row ids
            deletedata (boolean) -- delete the table rows if True, otherwise add new rows
        """
        with self._connection.cursor() as curs:
            for testid in ids:
                cmd_update = "update " + dbname + "." + tbname + \
                    " set lname='lname1' where id=" + str(testid)
                cmd_delete = "delete from " + dbname + \
                    "." + tbname + " where id=" + str(testid)
                if deletedata:
                    curs.execute(cmd_delete)
                else:
                    curs.execute(cmd_update)
                self.log.info(
                    "update_row: id: %s, status message: %s",
                    testid,
                    curs.statusmessage)
            self._connection.commit()

    def refresh_connection(self):
        """refresh connections"""
        self._connection.close()
        self._connect(self.sslenabled)

    def get_rows(self, dbname, tbname):
        """
        get rows ResultSet from table {tbname} in database {dbname}
        Args:
                dbname (str)        -- database name
                tbname (str)        -- table name
            Return:
                ResultSets for rows in table
        """
        self.refresh_connection()
        with self._connection.cursor() as curs:
            cmd = "SELECT id, lname, fname FROM " + dbname + "." + tbname + " order by id"
            curs.execute(cmd)
            return curs.fetchall()

    def close_connection(self):
        """close the connection to cockroachDB cluster"""
        self._connection.close()


class CockroachDB:
    """
    class has the functions to operate CockroachDB instances Under BigData Apps
    """
    test_step = TestStep()

    def __init__(self, admin_console, testcase):
        """Constructor for creating the cockroachDB object"""
        self._admin_console = admin_console
        self.__wizard = Wizard(admin_console)
        self.__instances = Instances(admin_console)
        self.__cockroachdb_server = CockroachDBServer(self._admin_console)
        self.__overview = Overview(self._admin_console)
        self.__tablegroups = TableGroups(self._admin_console)
        self.__commcell = testcase.commcell
        self.__backup = Backup(admin_console)
        self.__cockroachdb = None
        self.cockroachdb_name = testcase.cockroachdb_name
        self.access_nodes = testcase.tcinputs.get("access_nodes")
        self.cockroachdb_host = testcase.tcinputs.get("cockroachdb_host")
        self.plan_name = testcase.tcinputs.get("plan")
        self.db_username = testcase.db_username
        self.db_password = testcase.db_password
        self.cockroachdb__port = testcase.tcinputs.get("cockroachdb_port")
        self.use_iamrole = testcase.tcinputs.get("use_iamrole")
        self.use_ssl = testcase.tcinputs.get("use_ssl")
        self.s3_service_host = testcase.tcinputs.get("s3_service_host")
        self.s3_staging_path = testcase.tcinputs.get("s3_staging_path")
        self.aws_access_key = testcase.aws_access_key
        self.aws_secret_key = testcase.aws_secret_key
        self.sslrootcert = testcase.sslrootcert
        self.sslcert = testcase.sslcert
        self.sslkey = testcase.sslkey
        self.sslrootcert_on_controller = testcase.tcinputs.get(
            "sslrootcert_on_controller")
        self.sslcert_on_controller = testcase.tcinputs.get(
            "sslcert_on_controller")
        self.sslkey_on_controller = testcase.tcinputs.get(
            "sslkey_on_controller")
        self.dbname = testcase.dbname
        self.tablename = testcase.tablename

    def set_instanceparameter(self):
        """
        Creates a dictionary for test case inputs needed for creating cockroachDB instance
        """
        inputs = {}
        try:
            inputs["clustername"] = self.cockroachdb_name
            inputs["cockroachdbhost"] = self.cockroachdb_host
            inputs["accessnodes"] = self.access_nodes
            inputs["planname"] = self.plan_name
            inputs["dbusername"] = self.db_username
            inputs["dbpassword"] = self.db_password
            inputs["cockroachdbport"] = self.cockroachdb__port
            inputs["awsaccesskey"] = self.aws_access_key
            inputs["awssecretkey"] = self.aws_secret_key
            inputs["sslrootcert"] = self.sslrootcert
            inputs["sslcert"] = self.sslcert
            inputs["sslkey"] = self.sslkey
            inputs["s3servicehost"] = self.s3_service_host
            inputs["s3stagingpath"] = self.s3_staging_path
            inputs["useiamrole"] = self.use_iamrole
            inputs["usessl"] = self.use_ssl
            inputs["s3credential"] = "cockroachdbs3"
            return inputs
        except BaseException:
            raise Exception("failed to set inputs for interactive install")

    def refresh(self, wait_time=30):
        """ Refreshes the current page """
        self._admin_console.log.info(
            "%s Refreshes browser %s", "*" * 8, "*" * 8)
        self._admin_console.refresh_page()
        time.sleep(wait_time)

    @test_step
    def create_cockroachdb_instance(self):
        """create cockroachDB instance """
        self._admin_console.navigator.navigate_to_big_data()
        self.refresh()
        if self.__instances.is_instance_exists(self.cockroachdb_name):
            self.delete_cockroachdb_instance()

        _cockroachdb_server = self.__instances.add_cockroachdb_server()
        _instanceparam = self.set_instanceparameter()
        _cockroachdb_server.add_cockroachdb_instance(_instanceparam)

        self._admin_console.navigator.navigate_to_big_data()
        self.refresh()
        if not self.__instances.is_instance_exists(self.cockroachdb_name):
            raise CVTestStepFailure(
                "[%s] cockroachdb instanceis not getting created " %
                self.cockroachdb_name)
        self._admin_console.log.info(
            "Successfully Created [%s] cockroachdb instance",
            self.cockroachdb_name)

    @test_step
    def delete_cockroachdb_instance(self):
        """Delete cockroachDB instance and verify instance is deleted"""
        self._admin_console.navigator.navigate_to_big_data()
        self.refresh()
        self.__instances.delete_instance_name(self.cockroachdb_name)
        if self.__instances.is_instance_exists(self.cockroachdb_name):
            raise CVTestStepFailure(
                "[%s] CockroachDb instnace is not getting deleted" %
                self.cockroachdb_name)
        self._admin_console.log.info(
            "Deleted [%s] instance successfully",
            self.cockroachdb_name)

    @test_step
    def connect_to_db(self, ssl_enabled=True):
        """initiate cockroachdb connection """
        self.__cockroachdb = CockroachDBHelper(
            db_host=self.cockroachdb_host,
            db_username=self.db_username,
            db_password=self.db_password,
            db_port=self.cockroachdb__port,
            ssl_enabled=ssl_enabled,
            sslrootcert=self.sslrootcert_on_controller,
            sslcert=self.sslcert_on_controller,
            sslkey=self.sslkey_on_controller)

    @test_step
    def populate_test_data(self, dbname, tbname, rowids, clean_data=True):
        """
        populate test data
        Args:
            dbname          (str)     --    database name
            tbname           (str)    --    table name
            rowids            (list)    --    list of row ids
            clean_data    (boolean)   --    recreate database and tables if True
        """
        if clean_data:
            self.__cockroachdb.drop_database(dbname)
            self.__cockroachdb.create_database(dbname)
            self.__cockroachdb.create_table(dbname, tbname)
        self.__cockroachdb.add_data(dbname, tbname, rowids)

    @test_step
    def update_test_data(self, dbname, tbname, rowids, deletedata=False):
        """
        update test data
        Args:
            dbname          (str)     --    database name
            tbname           (str)    --    table name
            rowids            (list)    --    list of row ids
            deletedata    (boolean)   --    delete  if True
        """
        self.__cockroachdb.update_data(dbname, tbname, rowids, deletedata)

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
                                         2 - run backup from tablegroup action
            backuptype          (str):   backup type, "FULL" or "INCREMENTAL"
        """
        # Initiate backup job
        self._admin_console.navigator.navigate_to_big_data()
        self.refresh()
        if backupoption == 0:
            self.__instances.access_backup(self.cockroachdb_name)
        elif backupoption == 1:
            self.__instances.access_instance(self.cockroachdb_name)
            self._admin_console.click_button("Backup")
        else:
            self.__instances.access_instance(self.cockroachdb_name)
            self.__overview.access_tablegroups()
            self.__tablegroups.access_backup()
        self._admin_console.select_radio(id=backuptype)
        self._admin_console.click_button("Submit")
        _job_id = self._admin_console.get_jobid_from_popup()
        self.wait_for_job_completion(_job_id)

    def run_restore(
            self,
            destinstance,
            dbtables,
            srcdbname,
            destdbnames,
            restoreoption=0):
        """ Initiate restore job
        Args:
            destinstance    (str)    :    destination instance name
            restoreoption    (int)    :    0 - restore from instance action
                                           1 - restore from instance RPC
                                           2 - restore from tablegroup actions
                                           3 - restore from tablegroup RPC
            dbtables         (list)    :   list of databases or tables to be restored
            srcdbname        (string)  :   database name for the tables to be restored
            destdbnames      (list)    :   list of restore destination database names
        """
        self._admin_console.navigator.navigate_to_big_data()
        self.refresh()
        if restoreoption == 0:
            self.__instances.access_restore(self.cockroachdb_name)
        elif restoreoption == 1:
            self.__instances.access_instance(self.cockroachdb_name)
            self._admin_console.click_button(id="submit-btn")
        elif restoreoption == 2:
            self.__instances.access_instance(self.cockroachdb_name)
            self.__overview.access_tablegroups()
            self.__tablegroups.access_restore("default")
        else:
            self.__instances.access_instance(self.cockroachdb_name)
            self.__overview.access_tablegroups()
            self.__tablegroups.access_tablegroup("default")
            self._admin_console.click_button(id="submit-btn")
        if srcdbname is not None:
            _restore = self.__overview.select_restore_content(
                paths=dbtables, folder=srcdbname)
        else:
            _restore = self.__overview.select_restore_content(paths=dbtables)

        _restore.select_destination_instance(destinstance)
        _restore.select_overwrite_option()
        if srcdbname is None:
            for db in dbtables:
                i = dbtables.index(db)
                _restore.set_destination_path(
                    des_path=destdbnames[i], des_path_id=db)

        _restore.click_restore_and_confirm()
        _job_id = self._admin_console.get_jobid_from_popup()
        self.wait_for_job_completion(_job_id)

    def verify_restore(self, dbname, tbname, destdbname,
                       restoreoption=0, db_tb_option=0, restoredb=True):
        """
        verify restore with different options
        Args:
            dbname            (str)    :     database name to be restored
            tbname            (str)    :     table name to be restored
            destdbname        (str)    :     restore destination database name
            restoreoption     (int)    :     0 - restore from instance action
                                             1 - restore from instance RPC
                                             2 - restore from tablegroup actions
                                             3 - restore from tablegroup RPC
            db_tb_option      (int)    :     0 - drop destination database before restore
                                             1 - drop destination table before restore
                                             2 - truncate destination table before restore
            restoredb         (boolean) :    select database and restore if True
                                             select table and run restore if False
        """
        origdata = self.__cockroachdb.get_rows(dbname, tbname)

        if db_tb_option == 0:
            self.__cockroachdb.drop_database(destdbname)
        elif db_tb_option == 1:
            self.__cockroachdb.drop_table(destdbname, tbname)
        elif db_tb_option == 2:
            self.__cockroachdb.truncate_table(destdbname, tbname)

        if restoredb:
            self.run_restore(destinstance=self.cockroachdb_name,
                             dbtables=[self.dbname],
                             srcdbname=None,
                             destdbnames=[destdbname],
                             restoreoption=restoreoption)
        else:
            self.run_restore(destinstance=self.cockroachdb_name,
                             dbtables=["public." + tbname],
                             srcdbname=dbname,
                             destdbnames=None,
                             restoreoption=restoreoption)

        self.validate_restoredata(origdata, destdbname, tbname)

    def validate_restoredata(self, srcdata, dbname, tbname):
        """"validate restore data in DB
        Args:
            srcdata    (list)  - data from original tables
            dbname          (string)    - restore destination databasename
            tbname           (string)   - restore destination tablename
        """
        destresult = self.__cockroachdb.get_rows(dbname, tbname)
        if srcdata == destresult:
            self._admin_console.log.info("restored data match original data")
        else:
            raise CVTestStepFailure(
                "restored data does not match original data")

    @test_step
    def backup_from_instance_action(self, backuptype="INCREMENTAL"):
        """run backup job from instance actions
        Args:
            backuptype     (str)    : backup job type,  FULL or INCREMENTAL
        """
        self.run_backup(0, backuptype)

    @test_step
    def backup_from_instance_overview(self, backuptype="INCREMENTAL"):
        """run backup job from instance overview page
        Args:
            backuptype     (str)    : backup job type,  FULL or INCREMENTAL
        """
        self.run_backup(1, backuptype)

    @test_step
    def backup_from_tablegroup_action(self, backuptype="INCREMENTAL"):
        """run backup job from table group actions """
        self.run_backup(2, backuptype)

    @test_step
    def in_place_db_restore_from_instance_action(self, srcdbname, tbname):
        """verify in place db restore job from instance actions
        Args:
            srcdbname        (string)    - source database name
            tbname           (string)    - table name
        """
        self.verify_restore(dbname=srcdbname,
                            tbname=tbname,
                            destdbname=srcdbname,
                            restoreoption=0)

    @test_step
    def in_place_tb_restore_from_instance_action(self, srcdbname, tbname):
        """verify in place db restore job from instance actions
        Args:
            srcdbname        (string)    - source database name
            tbname           (string)    - table name
        """
        self.verify_restore(dbname=srcdbname,
                            tbname=tbname,
                            destdbname=srcdbname,
                            restoreoption=0,
                            restoredb=False)

    @test_step
    def in_place_db_restore_from_instance_RPC(self, srcdbname, tbname):
        """verify in place db restore from instance details Recovery point calendar
        Args:
            srcdbname        (string)    - source database name
            tbname           (string)    - table name
        """
        self.verify_restore(dbname=srcdbname,
                            tbname=tbname,
                            destdbname=srcdbname,
                            db_tb_option=1,
                            restoreoption=1)

    @test_step
    def in_place_table_restore_from_instance_RPC(self, srcdbname, tbname):
        """verify in place table restore from instance details Recovery point calendar
        Args:
            srcdbname        (string)    - source database name
            tbname           (string)    - table name
        """
        self.verify_restore(dbname=srcdbname,
                            tbname=tbname,
                            destdbname=srcdbname,
                            restoreoption=1,
                            db_tb_option=1,
                            restoredb=False)

    @test_step
    def in_place_db_restore_from_tablegroup_actions(self, srcdbname, tbname):
        """verify in place db restore from tablegroup actions
        Args:
            srcdbname        (string)    - source database name
            tbname           (string)    - table name
        """
        self.verify_restore(dbname=srcdbname,
                            tbname=tbname,
                            destdbname=srcdbname,
                            restoreoption=2,
                            db_tb_option=1)

    @test_step
    def in_place_table_restore_from_tablegroup_actions(
            self, srcdbname, tbname):
        """verify in place table restore from tablegroup actions
        Args:
            srcdbname        (string)    - source database name
            tbname           (string)    - table name
        """
        self.verify_restore(dbname=srcdbname,
                            tbname=tbname,
                            destdbname=srcdbname,
                            restoreoption=2,
                            db_tb_option=1,
                            restoredb=False)

    @test_step
    def out_of_place_db_restore_from_tablegroup_actions(
            self, srcdbname, tbname, destdbname):
        """verify out of place db restore from table group actions
        Args:
            srcdbname        (string)    - source database name
            tbname           (string)    - table name
            destdbname        (string)   - destination database name
        """
        self.verify_restore(dbname=srcdbname,
                            tbname=tbname,
                            destdbname=destdbname,
                            restoreoption=2,
                            db_tb_option=1)

    @test_step
    def drop_database(self, dbname):
        """drop database
        Args:
            dbname    (string)    :     database name which need be dropped
        """
        self.__cockroachdb.drop_database(dbname)

    @test_step
    def close_dbconnection(self):
        """close cockroachDB cluster connection"""
        self.__cockroachdb.close_connection()
