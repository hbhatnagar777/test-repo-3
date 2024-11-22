# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main helper file for performing Cloud Spanner operations

SpannerHelper: Helper class to perform sql server operations

SpannerHelper:

    __init__()              --  initializes SQL Server helper object

    get_spanner_databases() --  This function gets the databases in the Cloud Spanner Instance

    spanner_setup()         --  This function creates the spanner setup environment by creating databases and subclient.

    check_database()        --  This function checks the existence of a database

    create_databases()      --  This function creates as many databases with as many tables specified

    drop_databases()        --  This function drops the database(s)

    dump_database_to_file() --  This function writes the database to file for comparison

    database_compare()      --  This function compares database dump files for validation

    spanner_teardown()      --  This function performs teardown for Cloud Spanner on the items from spanner_setup.

"""

import os
import sys
import time
import random
import filecmp
from datetime import datetime
from google.cloud import spanner
from AutomationUtils.machine import Machine
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instances import SpannerInstance
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.db_instance_details import SpannerInstanceDetails


class SpannerHelper(object):
    """Helper class to perform Google Cloud Spanner operations"""

    def __init__(self,
                 _tcobject,
                 _spanner_instance,
                 _spanner_account_id,
                 _spanner_key,
                 _cloud_account=None
                 ):
        """Initializes SQLHelper object

        Args:
            _tcobject (:obj:'CVTestCase'): test case object

            _spanner_instance (str): Name of the Cloud Spanner instance

            _spanner_account_id (str): Email address of the Google cloud account

            _spanner_key (str): File path to the Cloud Spanner key JSON file

            _cloud_account (str): Cloud Account (Client Name) for the Cloud Spanner instance. Default: None

        """

        self.log = _tcobject.log
        self.spanner_client = spanner.Client.from_service_account_json(_spanner_key)
        self.spanner_instance = self.spanner_client.instance(_spanner_instance)
        
        _tcobject.instance_name = "{} [{}]".format(
            self.spanner_instance.name.split("/")[3],
            self.spanner_instance.name.split("/")[1]
        )
        self.instance_name = _tcobject.instance_name
        self.local_machine = Machine(commcell_object=_tcobject.commcell)

        self.tcobject = _tcobject
        self.spanner_account_id = _spanner_account_id
        self.spanner_key = _spanner_key

        self.access_node = None
        self.cloud_account = None
        self.plan_name = None

        if _cloud_account is not None:
            self.cloud_account = _cloud_account

        if _tcobject.tcinputs.get("PlanName"):
            self.plan_name = _tcobject.tcinputs["PlanName"]

        if _tcobject.tcinputs.get("AccessNode"):
            self.plan_name = _tcobject.tcinputs["AccessNode"]

        self.subclient = None
        self.tctime = None
        self.storagepolicy = None
        self.dbname = None
        self.content_list = None
        self.tcdir = None
        self.noof_dbs = None
        self.noof_tables_ffg = None
        self.noof_rows_table = None

    @property
    def get_spanner_databases(self):
        # get list of databases
        db_list = []
        for db in self.spanner_instance.list_databases():
            db_list.append(db.name.split("/")[-1])
        return db_list

    def spanner_setup(self,
                      noof_dbs=2,
                      noof_tables=2,
                      noof_rows_table=2,
                      **kwargs
                      ):
        """This function creates the Cloud Spanner setup environment by creating databases.

        Args:

            noof_dbs (int): Number of databases to create

            noof_tables (int): Number of tables per file groups to create

            noof_rows_table (int): Number of rows per table to create

        Keyword Args:

            add_instance (bool): Boolean whether to add the Cloud Spanner instance or not

            add_subclient (bool): Boolean whether to add subclient to Cloud Spanner instance or not

        """
        add_instance = None
        add_subclient = None

        if 'add_instance' in kwargs:
            add_instance = kwargs.get('add_instance')

        if 'add_subclient' in kwargs:
            add_subclient = kwargs.get('add_subclient')

        local_machine = self.local_machine
        tc_id = self.tcobject.id
        logdir = local_machine.client_object.log_directory

        time1 = (datetime.now()).strftime("%H:%M:%S")

        database_instances = DBInstances(self.tcobject.admin_console)
        spanner_instances = SpannerInstance(self.tcobject.admin_console)
        spanner_instance_details = SpannerInstanceDetails(self.tcobject.admin_console)

        try:
            self.tctime = time1

            # generate a random database name
            ransum = ""
            for i in range(1, 7):
                ransum = ransum + random.choice("abcdefghijklmnopqrstuvwxyz")
            dbname = ransum
            self.dbname = dbname

            # build temporary testcase logging directory and create it
            tcdir = logdir + "/" + tc_id + '-' + ransum
            tcdir = os.path.join(self.tcobject.log_dir, os.path.basename(os.path.normpath(tcdir)))
            local_machine.create_directory(tcdir)

            # build list for database creation
            content_list = []
            for i in range(1, noof_dbs + 1):
                db = dbname + repr(i)
                content_list.append(db)

            # perform database check if exists, if so, drop it first.
            if self.check_database(dbname):
                if not self.drop_databases(dbname):
                    raise Exception("Unable to drop the database")

            # create databases
            self.log.info("*" * 10 + " Creating database [{0}] ".format(dbname) + "*" * 10)
            if not self.create_databases(dbname, noof_dbs, noof_tables, noof_rows_table):
                raise Exception("Failed to create databases.")

            if add_instance:
                self.tcobject.client = self.tcobject.commcell.clients.get(self.cloud_account)
                self.tcobject.agent = self.tcobject.client.agents.get(self.tcobject.tcinputs['AgentName'])

                if self.instance_name not in self.tcobject.agent.instances.all_instances:
                    self.tcobject.admin_console.navigator.navigate_to_db_instances()
                    spanner_instances.add_spanner_instance(self, self.plan_name, self.cloud_account)
                    self.tcobject.agent.instances.refresh()
                self.tcobject.instance = self.tcobject.agent.instances.get(self.instance_name)
                self.tcobject.admin_console.navigator.navigate_to_db_instances()
                database_instances.select_instance(DBInstances.Types.CLOUD_DB, self.instance_name, self.cloud_account)

                if add_subclient:
                    self.log.info("*" * 10 + " Creating subclient " + "*" * 10)
                    spanner_instance_details.add_subclient(self, self.plan_name, content_list)

            self.content_list = content_list
            self.tcdir = tcdir
            self.noof_dbs = noof_dbs
            self.noof_tables_ffg = noof_tables
            self.noof_rows_table = noof_rows_table

        except Exception as excp:
            raise Exception("Exception raised in spanner_setup()\nError: '{0}'".format(excp))

    def check_database(self, database_name):
        """This function checks for the database.

        Args:
            database_name (str) : Database name

        Returns:
            bool: True for exists, else False

        """

        try:
            db_list = self.get_spanner_databases
            if database_name in db_list:
                return True
            return False

        except Exception as excp:
            raise Exception("Exception raised in check_database\nError: '{0}'".format(excp))

    def create_databases(self, database_name, noofdbs, nooftables, noofrowstable):
        """This function creates as many databases with as many tables specified

            The databases will be created with the names "databasename+dbnumber" with
            "tab+dbnumber+filegroupnumber+tablenumber+rownumber","tabm+dbnumber+tablenumber+rownumber"

            This creates as many number of dbs, tables and rows for which requested.

        Args:
            database_name (str): Database name
            noofdbs (int): Number of databases to be created
            nooftables (int): Number of tables for each database
            noofrowstable (int): Number of rows for each table

        Returns:
            bool: True for success, else False

        """
        import uuid
        import string

        def rand_str(length):
            """
            This function will randomize a string

            Args:
                length(int): Number of characters to make random string

            Returns:
                string: Randomized string
            """
            letters = string.ascii_lowercase
            return ''.join(random.choice(letters) for x in range(length))

        def rand_int():
            """
            This function returns a randomized integer from 0 to max python integer

            Returns:
                string: String of random integer
            """
            return str(random.randint(0, sys.maxsize))

        def rand_float():
            """
            This function returns a randomized float from 0 to 1024.00

            Returns:
                string: String of random float
            """
            return str(round(random.uniform(0, 10244.00), 2))

        def insert_rows(transaction, max_tries=5):
            """
            This function provides database row insertion for spanner tables

            Args:
                transaction(Transaction): Google Cloud Spanner transaction
                max_tries(int): Number of maximum tries to insert rows after failure. Default is 5.

            """
            while max_tries > 0:
                try:
                    rows_inserted = 0
                    for k in range(1, noofrowstable + 1):
                        row_query = "INSERT {0} (rowId,a,c,d,e,f,g,i,j,o,p,q,r,s,t,u,v,w,x,y,z,aa,bb,cc,ff,gg) " \
                                     "VALUES ({1},{4},'True','{5}','2009-09-19','2019-09-19 11:01:30.000'," \
                                    "'2009-02-12 12:30:15.1234567',{4},{7},32,'$30000','comm','cvcvcvcvcvcvc', {4}," \
                                    "'commvault','{2}{3}{1}',{7},'2009-09-02 03:50:00',1,'$1000','comm'," \
                                    "'2009-07-09 12:30:15.1234567',0,'{8}','commvault','{6}')"\
                                    .format(
                                        table, k, i, j, rand_int(), rand_str(5), rand_str(12), rand_float(),
                                        str(uuid.uuid4())
                                    )

                        row_ct = transaction.execute_update(row_query, timeout=60)
                        rows_inserted += row_ct
                    self.log.info("Inserted [{}] rows into table [{}]".format(rows_inserted, table))

                    return True
                except Exception as excp:
                    self.log.exception("Exception raised in insert_rows()\nError: '{0}'\nRetrying again.".format(excp))
                    max_tries -= 1

        try:
            for i in range(1, noofdbs + 1):
                db_to_create = database_name + str(i)
                database = self.spanner_instance.database(db_to_create)
                create_operation = database.create()

                self.log.info("Waiting for database creation to complete...")
                create_operation.result(120)
                self.log.info("Created database [{}] on instance [{}]".format(db_to_create, self.instance_name))

            # creating the tables for each db on mdf
            for i in range(1, noofdbs + 1):
                db_name = database_name + str(i)
                db_to_update = self.spanner_instance.database(db_name)

                for j in range(1, nooftables + 1):
                    table = "tab" + rand_str(3) + str(i) + str(j)
                    ddl_table_statement = \
                        "CREATE TABLE {0} (rowId int64 not null, a int64,c string(1024),d string(1024),e date," \
                        "f timestamp,g timestamp, i numeric,j float64,o int64,p string(1024),q string(1024)," \
                        "r string(1024),s numeric, t string(1024), u string(1024),v float64,w timestamp,x int64," \
                        "y string(1024),z string(1024), aa timestamp,bb int64, cc string(1024),ff string(1024)," \
                        "gg string(1024)) PRIMARY KEY (rowId)".format(table)

                    self.log.info("Creating table [{}] on database [{}]...".format(table, db_name))
                    table_create_operation = db_to_update.update_ddl([ddl_table_statement])
                    table_create_operation.result(120)
                    self.log.info("Table [{}] created on database [{}] successfully.".format(table, db_name))
                    time.sleep(0.5)

                    try:
                        db_to_update.run_in_transaction(insert_rows)
                        time.sleep(1)
                    except Exception:
                        db_to_update.run_in_transaction(insert_rows)

            return True
        except Exception as excp:
            raise Exception("Exception raised in insert_rows()\nError: '{0}'".format(excp))

    def drop_databases(self, database_name, useexistingdb=True):
        """This function drops the database(s)

        Args:
            database_name (str) : Database name
            useexistingdb (bool, optional) : Drop all databases with names that contain provided database_name

        Returns:
            bool: True for success, else False

        """

        if useexistingdb:
            db_list = self.get_spanner_databases
            for db in db_list:
                if database_name in db:
                    db_to_drop = self.spanner_instance.database(db)
                    db_to_drop.drop()

                    self.log.info("Dropping database [{}]...".format(db))
                    self.log.info(
                        "Database [{}] dropped from instance [{}].".format(db, self.instance_name)
                    )
        else:
            db_to_drop = self.spanner_instance.database(database_name)
            self.log.info("Dropping database [{}]...".format(database_name))
            db_to_drop.drop()
            self.log.info(
                "Database [{}] dropped from instance [{}].".format(database_name, self.instance_name)
            )
        return True

    def dump_database_to_file(self, file_name, database_name):
        """This function writes the database tables to file

        Args:
            file_name (str): File name
            database_name (str): Database name

        Returns:
            bool: True for Success else False

        """

        try:
            file_name = os.path.abspath(
                os.path.join(
                    self.tcobject.log_dir,
                    os.path.basename(os.path.normpath(self.tcdir)),
                    os.path.basename(file_name)
                )
            )
            file_handle = open(file_name, 'w')

            database = self.spanner_instance.database(database_name)

            with database.snapshot(multi_use=True) as snapshot:
                table_list_results = snapshot.execute_sql(
                    """SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA != 'INFORMATION_SCHEMA' AND TABLE_SCHEMA != 'SPANNER_SYS'"""
                )
                self.log.info("Results from table name read: ")
                for table_name in table_list_results:
                    table_name = table_name[0]

                    results = snapshot.execute_sql(
                        "SELECT * FROM {}".format(table_name)
                    )

                    self.log.info("Results from table: ")
                    for row in results:
                        self.log.info("[" + table_name + "] " + str(row))
                        file_handle.write("[" + table_name + "] " + str(row) + '\n')

                self.log.info("Writing the data to file: [{0}]".format(file_name))

            self.log.info("Successfully wrote data to file [{0}] ".format(file_name))
            return True

        except Exception as excp:
            raise Exception("Exception raised in dump_database_to_file()\nError: '{0}'".format(excp))

    def database_compare(self, dump_file1, dump_file2):
        """This function compares database dump files.

        Args:
            dump_file1 (str): File to be compared to file2
            dump_file2 (str): File to be compared to file1

        Returns:
            bool: True for success, False otherwise.

        """

        try:

            dump_file1 = os.path.basename(dump_file1)
            dump_file2 = os.path.basename(dump_file2)

            if filecmp.cmp(
                    os.path.abspath(
                        os.path.join(
                            self.tcobject.log_dir,
                            os.path.basename(os.path.normpath(self.tcdir)),
                            dump_file1
                        )
                    ),
                    os.path.abspath(
                        os.path.join(
                            self.tcobject.log_dir,
                            os.path.basename(os.path.normpath(self.tcdir)),
                            dump_file2
                        )
                    )
            ):
                self.log.info("Files {0} and {1} are identical".format(dump_file1, dump_file2))
                return True
            self.log.error("Files {0} and {1} differ!".format(dump_file1, dump_file2))
            return False

        except Exception as excp:
            raise Exception("Exception raised in database_compare()\nError: '{0}'".format(excp))

    def spanner_teardown(self):
        """
        This function performs standard teardown for Cloud Spanner automation on the basic created items from
        spanner_setup.

        """
        local_machine = self.local_machine
        database_instances = DBInstances(self.tcobject.admin_console)
        instance_details = DBInstanceDetails(self.tcobject.admin_console)

        try:
            # drop databases
            if not self.drop_databases(self.dbname):
                self.log.error("Unable to drop the database(s)")
            # delete directories
            tcdir_local_list = local_machine.get_folders_in_path(self.tcobject.log_dir)
            for tcdir_local in tcdir_local_list:
                if self.tcobject.id in tcdir_local:
                    local_machine.remove_directory(tcdir_local)

            self.tcobject.admin_console.navigator.navigate_to_db_instances()
            database_instances.select_instance(DBInstances.Types.CLOUD_DB, self.instance_name, self.cloud_account)
            if self.cloud_account is not None:
                instance_details.delete_instance()
            else:
                instance_details.delete_entity(self.subclient.name)
        except Exception as excp:
            self.log.exception("Exception raised in spanner_teardown()\nError: '{0}'".format(excp))
