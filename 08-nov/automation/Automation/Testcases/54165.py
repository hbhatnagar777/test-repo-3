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
        self.name = "SQL Restore - Unconditional Overwrite"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MSSQL
        self.feature = self.features_list.DATARECOVERY
        self.show_to_user = True

        self.tcinputs = {
            "SQLServerUser": None,
            "SQLServerPassword": None
        }

        self.sqlhelper = None
        self.sqlmachine = None

    def run(self):
        """Main function for test case execution"""
        clientname = self.client.client_name
        instancename = self.instance.instance_name
        sqluser = self.tcinputs["SQLServerUser"]
        sqlpass = self.tcinputs["SQLServerPassword"]
        self.sqlhelper = SQLHelper(self, clientname, instancename, sqluser, sqlpass)
        self.sqlmachine = Machine(self.client)

        try:
            self.sqlhelper.sql_setup(noof_dbs=1)
            self.subclient = self.sqlhelper.subclient

            # run a full backup
            self.sqlhelper.sql_backup('Full')
            # run a log backup
            jobid_log1 = self.sqlhelper.sql_backup('Transaction_Log')

            # check backup level for log job
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(jobid_log1, multidb=False)
            if str(backuplevel) != "Transaction Log":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                self.log.info("Backup level confirmed: " + str(backuplevel))

            # get backup end time of log from CS db
            log1_end_time = self.sqlhelper.get_sql_backup_end_time(jobid_log1)
            self.log.info("Job End time - " + log1_end_time)

            # build dict with original database names and new names
            db1_restore = self.sqlhelper.dbname + str(1)
            db1_restore_list = [db1_restore]

            database_name_list = []

            database_name_dict = {
                'database_names': {
                    sqlconstants.DATABASE_ORIG_NAME: db1_restore,
                    sqlconstants.DATABASE_NEW_NAME: db1_restore
                }
            }
            database_name_list.append(database_name_dict)

            # get the file path list for restore
            restore_path_list = self.sqlhelper.get_file_list_restore(database_name_list,
                                                                     restore_path=self.sqlhelper.tcdir,
                                                                     filerename=True)
            # kill db connections and restore db1 using job_id_log1
            self.sqlhelper.dbinit.kill_db_connections(self.sqlhelper.dbname, self.sqlhelper.noof_dbs, True)

            self.log.info("*" * 10 + " Run Restore to same instance - new file names & new path" + "*" * 10)
            self.sqlhelper.sql_restore(db1_restore_list, to_time=log1_end_time, restore_path=restore_path_list)

            # verify database is online after restore
            if not self.sqlhelper.dbvalidate.is_db_online(db1_restore, useexistingdb=False):
                raise Exception("Databases are not online on source instance.")

            # verify db is utilizing new location
            dbpath1 = self.sqlhelper.dbvalidate.db_path(db1_restore)[1]
            if not any(self.sqlhelper.tcdir in s for s in dbpath1):
                raise Exception("Restored database was not restored to its new location.")

            # run full backup and verify backup
            jobid_full2 = self.sqlhelper.sql_backup('Full')
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(jobid_full2, multidb=False)
            if str(backuplevel) != "Full":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                self.log.info("Backup level confirmed: {0} ".format(backuplevel))

            # delete all databases
            if not self.sqlhelper.dbinit.drop_databases(self.sqlhelper.dbname):
                self.log.error("Unable to drop the database")

            # delete directory
            self.sqlmachine.remove_directory(self.sqlhelper.tcdir)

            # delete subclient
            self.instance.subclients.delete(self.subclient.subclient_name)

            # create the setup again and run another set of tests
            self.sqlhelper.sql_setup(noof_dbs=3)
            self.subclient = self.sqlhelper.subclient

            # get table shuffled list
            returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                100, self.sqlhelper.noof_dbs, self.sqlhelper.noof_ffg_db, self.sqlhelper.noof_tables_ffg)
            if not returnstring:
                raise Exception("Error in while generating the random number.")

            # full backup and verify full backup
            jobid_full2 = self.sqlhelper.sql_backup('Full')

            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(jobid_full2, multidb=False)
            if str(backuplevel) != "Full":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                self.log.info("Backup level confirmed: " + str(backuplevel))

            # modify dbs, run diff and verify diff backup
            self.sqlhelper.modifydatabase.modify_db_for_diff(self.sqlhelper.dbname, list1, list2, list3)
            jobid_diff1 = self.sqlhelper.sql_backup('Differential')

            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(jobid_diff1, multidb=False)
            if str(backuplevel) != "Differential":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                self.log.info("Backup level confirmed: " + str(backuplevel))

            # modify dbs, run log and verify log backup - use this backup time for restores
            self.sqlhelper.modifydatabase.modify_db_for_inc(self.sqlhelper.dbname, list1, list2, list3)
            jobid_log2 = self.sqlhelper.sql_backup('Transaction_Log')

            # get backup end time of log from CS db
            log2_end_time = self.sqlhelper.get_sql_backup_end_time(jobid_log2)
            self.log.info("Job End time - " + log2_end_time)

            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(jobid_log2, multidb=False)
            if str(backuplevel) != "Transaction Log":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                self.log.info("Backup level confirmed: " + str(backuplevel))

            # kill db connections, restore db1 with no overwrite (should fail because no overwrite)
            db1_restore = self.sqlhelper.dbname + str(1)
            db1_restore_list = [db1_restore]
            self.sqlhelper.dbinit.kill_db_connections(self.sqlhelper.dbname, self.sqlhelper.noof_dbs, True)
            database_name_list = []

            database_name_dict = {
                'database_names': {
                    sqlconstants.DATABASE_ORIG_NAME: db1_restore,
                    sqlconstants.DATABASE_NEW_NAME: db1_restore
                }
            }
            database_name_list.append(database_name_dict)

            self.log.info("*" * 10 + " Run Restore in place of 1 database with no overwrite " + "*" * 10)
            self.sqlhelper.sql_restore(db1_restore_list, to_time=log2_end_time, timeout=2,
                                       job_delay_reason="overwrite", overwrite=False)

            # restore db1 with overwrite
            self.log.info("*" * 10 + " Run Restore in place of 1 database with overwrite" + "*" * 10)
            self.sqlhelper.sql_restore(db1_restore_list, to_time=log2_end_time)

            # verify database is online after restore
            if not self.sqlhelper.dbvalidate.is_db_online(db1_restore, useexistingdb=False):
                raise Exception("Databases are not online on source instance.")

            # drop databases 1 + 3
            for i in range(1, 4):
                if i == 2:
                    continue
                db = self.sqlhelper.dbname + str(i)
                if not self.sqlhelper.dbinit.drop_databases(db, useexistingdb=False):
                    raise Exception("Unable to drop the database {[0]}".format(db))

            # restore all dbs no overwrite (should expect CWE because db2 existed and no overwrite used)
            self.log.info("*" * 10 + " Run Restore in place with no overwrite" + "*" * 10)
            self.sqlhelper.sql_restore(self.subclient.content, to_time=log2_end_time, overwrite=False, restore_count=2)

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""

        self.sqlhelper.sql_teardown()
