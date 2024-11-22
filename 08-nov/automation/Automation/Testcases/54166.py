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
        self.name = "SQL Step Restore - General"
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
            jobid_full1 = self.sqlhelper.sql_backup('Full')

            # get backup end time of log from CS db
            full1_end_time = self.sqlhelper.get_sql_backup_end_time(jobid_full1)
            self.log.info("Job End time - [{0}] ".format(full1_end_time))

            # add table to database
            dbname = self.sqlhelper.dbname + str(1)
            self.sqlhelper.modifydatabase.create_table(dbname, 'log1')

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

            # add 2nd table to the database
            self.sqlhelper.modifydatabase.create_table(dbname, 'log2')

            # run a 2nd log backup
            jobid_log2 = self.sqlhelper.sql_backup('Transaction_Log')

            # check backup level for log job
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(jobid_log2)
            if str(backuplevel) != "Transaction Log":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                self.log.info("Backup level confirmed: " + str(backuplevel))

            # get backup end time of log from CS db
            log2_end_time = self.sqlhelper.get_sql_backup_end_time(jobid_log2)
            self.log.info("Job End time - " + log2_end_time)

            # add 3rd table to the database
            self.sqlhelper.modifydatabase.create_table(dbname, 'log3')

            # run a 3rd log backup
            jobid_log3 = self.sqlhelper.sql_backup('Transaction_Log')

            # check backup level for log job
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(jobid_log3)
            if str(backuplevel) != "Transaction Log":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                self.log.info("Backup level confirmed: " + str(backuplevel))

            # get backup end time of log from CS db
            log3_end_time = self.sqlhelper.get_sql_backup_end_time(jobid_log3)
            self.log.info("Job End time - " + log3_end_time)

            # kill db connections and restore db1 using job_id_full1
            self.sqlhelper.dbinit.kill_db_connections(self.sqlhelper.dbname, self.sqlhelper.noof_dbs, True)

            self.log.info("*" * 10 + " Run Restore with Standby: Restore Full backup" + "*" * 10)
            self.sqlhelper.sql_restore(self.sqlhelper.subcontent, to_time=full1_end_time,
                                       sql_recover_type=sqlconstants.STATE_STANDBY, undo_path=self.sqlhelper.tcdir)

            # get list of tables for the database
            table_name_list = self.sqlhelper.dbvalidate.get_database_tables(dbname)

            # validate restore was done just for full job
            if ('log1' in table_name_list) or ('log2' in table_name_list) or ('log3' in table_name_list):
                raise Exception("Restore failed: restore from only Full backup did not happen.")

            # kill db connections and restore db1 using job_id_log1
            self.sqlhelper.dbinit.kill_db_connections(self.sqlhelper.dbname, self.sqlhelper.noof_dbs, True)

            self.log.info("*" * 10 + " Run Restore with Standby: Step Restore 1st Log" + "*" * 10)
            self.sqlhelper.sql_restore(self.sqlhelper.subcontent, to_time=log1_end_time,
                                       sql_restore_type=sqlconstants.STEP_RESTORE,
                                       sql_recover_type=sqlconstants.STATE_STANDBY, undo_path=self.sqlhelper.tcdir)

            # get list of tables for the database
            table_name_list = self.sqlhelper.dbvalidate.get_database_tables(dbname)

            # validate restore was done for 1st log job
            if ('log1' not in table_name_list) or ('log2' in table_name_list) or ('log3' in table_name_list):
                raise Exception("Restore failed: Step restore to 1st log backup failed.")

            # kill db connections and restore db1 using job_id_log2
            self.sqlhelper.dbinit.kill_db_connections(self.sqlhelper.dbname, self.sqlhelper.noof_dbs, True)

            self.log.info("*" * 10 + " Run Restore with Standby: Step Restore 2nd Log" + "*" * 10)
            self.sqlhelper.sql_restore(self.sqlhelper.subcontent, to_time=log2_end_time,
                                       sql_restore_type=sqlconstants.STEP_RESTORE,
                                       sql_recover_type=sqlconstants.STATE_STANDBY, undo_path=self.sqlhelper.tcdir)

            # get list of tables for the database
            table_name_list = self.sqlhelper.dbvalidate.get_database_tables(dbname)

            # validate restore was done for 2nd log job
            if ('log1' not in table_name_list) or ('log2' not in table_name_list) or ('log3' in table_name_list):
                raise Exception("Restore failed: Step restore to 2nd log backup failed.")

            # kill db connections and restore db1 using job_id_log3
            self.sqlhelper.dbinit.kill_db_connections(self.sqlhelper.dbname, self.sqlhelper.noof_dbs, True)

            self.log.info("*" * 10 + " Run Restore with Standby: Step Restore 3rd Log" + "*" * 10)
            self.sqlhelper.sql_restore(self.sqlhelper.subcontent, to_time=log3_end_time,
                                       sql_restore_type=sqlconstants.STEP_RESTORE,
                                       sql_recover_type=sqlconstants.STATE_RECOVER)

            # get list of tables for the database
            table_name_list = self.sqlhelper.dbvalidate.get_database_tables(dbname)

            # validate restore was done for 3rd log job
            if not ('log1' in table_name_list) and ('log2' in table_name_list) and ('log3' in table_name_list):
                raise Exception("Restore failed: Step restore to 2nd log backup failed.")

            # verify database is online after restore
            if not self.sqlhelper.dbvalidate.is_db_online(dbname, useexistingdb=False):
                raise Exception("Databases are not online.")

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""

        self.sqlhelper.sql_teardown()
