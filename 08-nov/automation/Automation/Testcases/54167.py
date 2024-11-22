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
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from Application.SQL import sqlconstants
from Application.SQL.sqlhelper import SQLHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import SnapShotEngineNames


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of SQL Server backup and restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL Snap - Restore with NORECOVER"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MSSQL
        self.feature = self.features_list.DATARECOVERY
        self.show_to_user = True

        self.tcinputs = {
            "MediaAgentName": None,
            "LibraryName": None,
            "SnapEngineName": None,
            "DirectoryPathOnLUN": None,
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
        media_agent = self.tcinputs["MediaAgentName"]
        library_name = self.tcinputs["LibraryName"]
        snap_engine_name = self.tcinputs["SnapEngineName"]
        snap_dir = self.tcinputs["DirectoryPathOnLUN"]
        self.sqlhelper = SQLHelper(self, clientname, instancename, sqluser, sqlpass)
        self.sqlmachine = Machine(self.client)

        try:
            sqldump_file1 = "before_backup_full.txt"
            sqldump_file2 = "after_restore.txt"

            self.sqlhelper.sql_setup(noof_dbs=1, db_path=snap_dir, snap_setup=True, library_name=library_name,
                                     media_agent=media_agent)
            self.subclient = self.sqlhelper.subclient

            if not SnapShotEngineNames(snap_engine_name):
                self.log.info("Snap Engine Name [{0}] is invalid. Please enter correct Snap Engine Name"
                              .format(snap_engine_name))

            self.subclient.enable_intelli_snap(snap_engine_name)

            # get table shuffled list
            returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                100, self.sqlhelper.noof_dbs, self.sqlhelper.noof_ffg_db, self.sqlhelper.noof_tables_ffg)
            if not returnstring:
                raise Exception("Error in while generating the random number.")

            # run a full backup
            jobid_full1 = self.sqlhelper.sql_backup('Full')

            # get backup end time of log from CS db
            full1_end_time = self.sqlhelper.get_sql_backup_end_time(jobid_full1)
            self.log.info("Job End time - [{0}] ".format(full1_end_time))

            # modify dbs, run log and verify log backup - use this backup time for restores
            self.sqlhelper.modifydatabase.modify_db_for_inc(self.sqlhelper.dbname, list1, list2, list3)

            # run a log backup
            jobid_log1 = self.sqlhelper.sql_backup('Transaction_Log')

            # check backup level for log job
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(jobid_log1)
            if str(backuplevel) != "Transaction Log":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                self.log.info("Backup level confirmed: " + str(backuplevel))

            # get backup end time of log from CS db
            log1_end_time = self.sqlhelper.get_sql_backup_end_time(jobid_log1)
            self.log.info("Job End time - " + log1_end_time)

            # write the original database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                                                             self.sqlhelper.dbname, list1, list2, list3, 'FULL'):
                raise Exception("Failed to write database to file.")

            # delete all databases
            if not self.sqlhelper.dbinit.drop_databases(self.sqlhelper.dbname):
                self.log.error("Unable to drop the database")

            self.log.info("*" * 10 + " Run Restore with NoRecovery: Restore Full backup" + "*" * 10)
            self.sqlhelper.sql_restore(self.sqlhelper.subcontent, to_time=full1_end_time,
                                       sql_recover_type=sqlconstants.STATE_NORECOVER)

            dbname = self.sqlhelper.dbname + str(1)

            database_state = self.sqlhelper.dbvalidate.get_database_state(dbname)
            if not database_state == "RESTORING":
                raise Exception("Database [{0}] is not in RESTORING state. NoRecovery restore was not successful"
                                .format(dbname))

            self.log.info("*" * 10 + " Run Restore with NoRecovery: Restore Log backup" + "*" * 10)
            self.sqlhelper.sql_restore(self.sqlhelper.subcontent, to_time=log1_end_time,
                                       sql_recover_type=sqlconstants.STATE_NORECOVER)

            database_state = self.sqlhelper.dbvalidate.get_database_state(dbname)
            if not database_state == "RESTORING":
                raise Exception("Database [{0}] is not in RESTORING state. NoRecovery restore was not successful"
                                .format(dbname))

            self.log.info("*" * 10 + " Run Restore with Recovery Only" + "*" * 10)
            self.sqlhelper.sql_restore(self.sqlhelper.subcontent, to_time=log1_end_time,
                                       sql_restore_type=sqlconstants.RECOVER_ONLY)

            # verify database is online after restore
            if not self.sqlhelper.dbvalidate.is_db_online(dbname, useexistingdb=False):
                raise Exception("Databases are not online.")

            # write the restored database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(os.path.join(self.sqlhelper.tcdir, sqldump_file2),
                                                             self.sqlhelper.dbname, list1, list2, list3, 'FULL'):
                raise Exception("Failed to write database to file.")

            # compare original and restored databases
            self.log.info("*" * 10 + " Validating content " + "*" * 10)
            if not self.sqlhelper.dbvalidate.db_compare(os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                                                        os.path.join(self.sqlhelper.tcdir, sqldump_file2)):
                raise Exception("Failed to compare both files.")

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""

        self.sqlhelper.sql_teardown()
