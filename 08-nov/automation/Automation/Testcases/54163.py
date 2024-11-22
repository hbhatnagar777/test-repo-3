# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import os
import random
import datetime
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from Application.SQL import sqlconstants
from Application.SQL.sqlhelper import SQLHelper
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of SQL Server backup and restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL - Data Recovery - Advanced - Out-of-place - Rename a database and data files"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MSSQL
        self.feature = self.features_list.DATARECOVERY
        self.show_to_user = False

        self.sqlhelper = None
        self.destsqlhelper = None
        self.destsqlmachine = None
        self.dest_job_results = None
        self.sqlmachine = None
        self.tcdir = None
        self.restore_path_source = None
        self.restore_path_dest = None
        self.dbname = None
        self.subclient_default = None

        self.tcinputs = {
            "StoragePolicyName": None,
            "SQLServerUser": None,
            "SQLServerPassword": None,
            "DestinationSQLServerUser": None,
            "DestinationSQLServerPassword": None,
            "DestinationInstanceName": None
        }

    def run(self):
        """Main function for test case execution"""

        log = self.log
        logdir = self._log_dir
        time1 = (datetime.datetime.now()).strftime("%H:%M:%S")
        clientname = self.client.client_name
        instancename = self.instance.instance_name
        dest_instancename = self.tcinputs["DestinationInstanceName"]

        if dest_instancename.find("\\") > -1:
            dest_clientname = dest_instancename.split('\\', 1)[0]
        else:
            dest_clientname = dest_instancename

        subclientname = "Subclient{0}_{1}".format(self.id, time1)
        sqluser = self.tcinputs["SQLServerUser"]
        sqlpass = self.tcinputs["SQLServerPassword"]
        dest_sqluser = self.tcinputs["DestinationSQLServerUser"]
        dest_sqlpass = self.tcinputs["DestinationSQLServerPassword"]
        storagepolicy = self.tcinputs["StoragePolicyName"]
        self.sqlmachine = Machine(self.client)
        self.destsqlmachine = Machine(dest_clientname, self.commcell)

        self.sqlhelper = SQLHelper(self, clientname, instancename, sqluser, sqlpass)
        self.destsqlhelper = SQLHelper(self, clientname, dest_instancename, dest_sqluser, dest_sqlpass)
        dest_client = self.commcell.clients.get(dest_clientname)
        self.dest_job_results = dest_client.job_results_directory

        sys_db_list = ["master", "msdb", "model"]

        ransum = ""
        for i in range(1, 7):
            ransum = ransum + random.choice("abcdefghijklmnopqrstuvwxyz")
        self.dbname = ransum

        try:
            self.tcdir = os.path.normpath(os.path.join(logdir, self.id + '-' + ransum))

            noofdbs = 1
            nooffilegroupsforeachdb = 3
            nooffilesforeachfilegroup = 3
            nooftablesforeachfilegroup = 5
            noofrowsforeachtable = 6

            log.info("Started executing {0} testcase".format(self.id))

            # Build restore paths for source and destination instances.  They both need to be in
            # separate locations to avoid conflicts in cases source and destination instances are the same machine.
            self.restore_path_source = self.tcdir
            self.restore_path_dest = self.dest_job_results + "/" + "sql_automation" + "/" + str(self.id) + '-' + ransum

            if not self.sqlmachine.create_directory(self.restore_path_source):
                raise Exception("Failed to create first restore path. ")

            if not self.destsqlmachine.create_directory(self.restore_path_dest):
                raise Exception("Failed to create second restore path")

            # SQL linux restores require that the destination path of the databases is owned by mssql user.
            if self.sqlmachine.os_info.lower() == "unix":
                if not self.sqlmachine.change_folder_owner("mssql", self.restore_path_source):
                    raise Exception("Failed to change directory owner. ")

            if self.destsqlmachine.os_info.lower() == "unix":
                if not self.destsqlmachine.change_folder_owner("mssql", self.restore_path_dest):
                    raise Exception("Failed to change directory owner. ")

            subcontent = []
            for i in range(1, int(noofdbs) + 1):
                db = self.dbname + repr(i)
                subcontent.append(db)

            # perform database check if exists, if so, drop it first. SOURCE INSTANCE
            if self.sqlhelper.dbinit.check_database(self.dbname):
                if not self.sqlhelper.dbinit.drop_databases(self.dbname):
                    raise Exception("Unable to drop the database")

            # create databases on SOURCE INSTANCE
            log.info("*" * 10 + " Creating database [{0}] ".format(self.dbname) + "*" * 10)
            if not self.sqlhelper.dbinit.db_new_create(self.dbname, noofdbs, nooffilegroupsforeachdb,
                                                       nooffilesforeachfilegroup, nooftablesforeachfilegroup,
                                                       noofrowsforeachtable):
                raise Exception("Failed to create databases.")

            # Check if system databases are part of default subclient contents & remove if they are
            self.subclient_default = self.instance.subclients.get("default")  # create subclient object for default
            if len(self.subclient_default.content) > 0:
                subclient_db_list = self.subclient_default.content

                db_sc_list = []
                for scdb in subclient_db_list:
                    if scdb in sys_db_list:
                        db_sc_list.append(scdb)

                if len(db_sc_list) > 0:
                    log.info("Deleting system databases from default subclient")
                    self.subclient_default.update_content(subclient_db_list, 3)

            # create subclient
            log.info("*" * 10 + " Creating subclient [{0}] ".format(subclientname) + "*" * 10)
            if not self.sqlhelper.create_subclient(subclientname, subcontent, storagepolicy):
                self._subclient = self.instance.subclients.get(subclientname)
                raise Exception("Failed to create subclient.")
            else:
                self._subclient = self.instance.subclients.get(subclientname)

            # run a FULL backup
            job_id = self.sqlhelper.sql_backup('Full')

            # check backup level for FULL
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id, multidb=False)
            if str(backuplevel) != "Full":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                log.info("Backup level confirmed: " + str(backuplevel))

            # get backup end time of Full from CS db
            fullend = self.sqlhelper.get_sql_backup_end_time(job_id)
            log.info("Job End time - " + fullend)

            # build dict with original database names and new names
            database_name_list = []
            for content in subcontent:
                database_name_dict = {
                    'database_names': {
                        sqlconstants.DATABASE_ORIG_NAME: content,
                        sqlconstants.DATABASE_NEW_NAME: content + "_renamed"
                    }
                }

                database_name_list.append(database_name_dict)

            restore_path_list = self.sqlhelper.get_file_list_restore(database_name_list, filerename=True)
            restore_path_list_dest = self.sqlhelper.get_file_list_restore(database_name_list,
                                                                          restore_path=self.restore_path_dest,
                                                                          filerename=True)

            # kill db connections
            if not self.sqlhelper.dbinit.kill_db_connections(self.dbname, noofdbs, True):
                raise Exception("Unable to kill database connections")

            # run restore in place job - based on Full time
            log.info("*" * 10 + " Run Restore to same instance - new DB name & new file names & orig path" + "*" * 10)
            if not self.sqlhelper.sql_restore(self.subclient.content, to_time=fullend, restore_path=restore_path_list):
                raise Exception("Restore was not successful!")

            # Checking if databases are online
            for i in range(1, int(noofdbs) + 1):
                db = self.dbname + repr(i) + "_renamed"
                if not self.sqlhelper.dbvalidate.is_db_online(db, useexistingdb=False):
                    raise Exception("Databases are not online on source instance.")

            # run restore in place job - based on Full time to destination instance
            log.info("*" * 10 + " Run Restore to diff instance - new DB name & new file names & new path " + "*" * 10)
            if not self.sqlhelper.sql_restore(self.subclient.content, to_time=fullend,
                                              restore_path=restore_path_list_dest,
                                              destination_instance=dest_instancename):
                raise Exception("Restore was not successful!")

            # Checking if databases are online
            for i in range(1, int(noofdbs) + 1):
                db = self.dbname + repr(i) + "_renamed"
                if not self.destsqlhelper.dbvalidate.is_db_online(db, useexistingdb=False):
                    raise Exception("Databases are not online on destination instance.")

            # delete subclient
            self.instance.subclients.delete(self.subclient.subclient_name)

            # create subclient with system dbs
            log.info("*" * 10 + " Creating subclient [{0}] ".format(subclientname) + "*" * 10)
            if not self.sqlhelper.create_subclient(subclientname, sys_db_list, storagepolicy):
                self._subclient = self.instance.subclients.get(subclientname)
                raise Exception("Failed to create subclient.")
            else:
                self._subclient = self.instance.subclients.get(subclientname)

            # make sure the renamed system databases from previous run are not online
            for i in ["master_renamed", "model_renamed", "msdb_renamed"]:
                if self.sqlhelper.dbvalidate.is_db_online(i, useexistingdb=False):
                    raise Exception("Databases are already online.  Probably from a previous run.")

            # run a FULL backup
            job_id = self.sqlhelper.sql_backup('Full')

            # check backup level for FULL
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id, multidb=False)
            if str(backuplevel) != "Full":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                log.info("Backup level confirmed: " + str(backuplevel))

            # get backup end time of Full from CS db
            fullend = self.sqlhelper.get_sql_backup_end_time(job_id)
            log.info("Job End time - " + fullend)

            # get system database file paths
            sys_database_name_list = []
            for content in sys_db_list:
                sys_database_name_dict = {
                    'database_names': {
                        sqlconstants.DATABASE_ORIG_NAME: content,
                        sqlconstants.DATABASE_NEW_NAME: content + "_renamed"
                    }
                }
                sys_database_name_list.append(sys_database_name_dict)

            sys_restore_path_list = self.sqlhelper.get_file_list_restore(sys_database_name_list, filerename=True)
            sys_restore_path_list_dest = self.sqlhelper.get_file_list_restore(sys_database_name_list,
                                                                              restore_path=self.restore_path_dest,
                                                                              filerename=True)

            # run restore in place job - based on Full time
            log.info("*" * 10 + " Run Restore of system databases to new names" + "*" * 10)
            if not self.sqlhelper.sql_restore(self.subclient.content, to_time=fullend,
                                              restore_path=sys_restore_path_list):
                raise Exception("Restore was not successful!")

            # make sure the renamed system databases from restore are online
            for i in ["master_renamed", "model_renamed", "msdb_renamed"]:
                if not self.sqlhelper.dbvalidate.is_db_online(i, useexistingdb=False):
                    raise Exception("Databases are not online.")

            # get the creation time of the tempdb on destination instance
            tempdb_time_before = self.destsqlhelper.dbvalidate.get_tempdb_create_time()
            if not tempdb_time_before:
                raise Exception("Could not get the tempdb creation time.")

            # run restore in place job - based on Full time
            log.info("*" * 10 + " Run Restore of system databases to new names on destination instance" + "*" * 10)
            if not self.sqlhelper.sql_restore(self.subclient.content, to_time=fullend,
                                              restore_path=sys_restore_path_list_dest,
                                              destination_instance=dest_instancename):
                raise Exception("Restore was not successful!")

            # make sure the renamed system databases from restore are online
            for i in ["master_renamed", "model_renamed", "msdb_renamed"]:
                if not self.destsqlhelper.dbvalidate.is_db_online(i, useexistingdb=False):
                    raise Exception("Databases are not online.")

            # get the creation time of the tempdb on destination instance
            tempdb_time_after = self.destsqlhelper.dbvalidate.get_tempdb_create_time()
            if not tempdb_time_after:
                raise Exception("Could not get the tempdb creation time.")

            if tempdb_time_before != tempdb_time_after:
                raise Exception("SQL services were stopped on destination when they weren't supposed to be.")
            else:
                log.info("SQL services were not stopped on destination as expected with system db rename.")

            log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""

        log = self.log
        sys_db_list = ["master", "msdb", "model"]

        # drop databases
        if not self.sqlhelper.dbinit.drop_databases(self.dbname):
            log.error("Unable to drop the dataBase on source")
        # drop dest instance databases
        if not self.destsqlhelper.dbinit.drop_databases(self.dbname):
            log.error("Unable to drop the dataBase on destination")
        # drop system databases on source
        for db in sys_db_list:
            db += "_renamed"
            if not self.sqlhelper.dbinit.drop_databases(db, useexistingdb=False):
                log.error("Unable to drop the system dataBases on source")
            # drop system databases on destination
            if not self.destsqlhelper.dbinit.drop_databases(db, useexistingdb=False):
                log.error("Unable to drop the system dataBases on destination")
        # delete directory
        self.sqlmachine.remove_directory(self.restore_path_source)
        # delete destination directory
        self.destsqlmachine.remove_directory(self.restore_path_dest)
        # delete subclient
        self.instance.subclients.delete(self.subclient.subclient_name)
