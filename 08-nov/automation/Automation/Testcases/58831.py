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
from AutomationUtils.cvtestcase import CVTestCase
from Application.SQL.sqlhelper import SQLHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of SQL Server backup and restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL Restore - Copy Only Backup"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MSSQL
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = False

        self.sqlhelper = None
        self.sqlmachine = None

        self.tcinputs = {
            "SQLServerUser": None,
            "SQLServerPassword": None
        }

    def run(self):
        """Main function for test case execution"""

        log = self.log

        clientname = self.client.client_name
        instancename = self.instance.instance_name
        sqluser = self.tcinputs["SQLServerUser"]
        sqlpass = self.tcinputs["SQLServerPassword"]

        self.sqlmachine = Machine(self.client)
        self.sqlhelper = SQLHelper(self, clientname, instancename, sqluser, sqlpass)

        try:
            sqldump_file1 = "before_backup_full.txt"
            sqldump_file2 = "after_restore.txt"

            log.info("Started executing {0} testcase".format(self.id))

            self.sqlhelper.sql_setup(noof_dbs=3)
            self.subclient = self.sqlhelper.subclient

            # get table shuffled list
            returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                100, self.sqlhelper.noof_dbs, self.sqlhelper.noof_ffg_db, self.sqlhelper.noof_tables_ffg
            )
            if not returnstring:
                raise Exception("Error in while generating the random number.")

            # add table to database for verification after restore
            self.sqlhelper.modifydatabase.create_table(self.sqlhelper.dbname + "1", "Verify" + self.id)

            # run a full job
            self.sqlhelper.sql_backup('full')

            # delete table from before.. restore should not have this table from previous cycle
            self.sqlhelper.modifydatabase.drop_table(self.sqlhelper.dbname + "1", "Verify" + self.id)

            # run a full copy only job
            job_id = self.sqlhelper.sql_backup('full', ["copy_only"])

            # check backup level for Full - should be full copy only
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id)
            if str(backuplevel) != "Full(Copy-Only)":
                raise Exception("Wrong backup level of the database detected in the job")
            log.info("Backup level confirmed: " + str(backuplevel))

            # run a TL backup
            job_id = self.sqlhelper.sql_backup('transaction_log')

            # check backup level for TL1
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id)
            if str(backuplevel) != "Transaction Log":
                raise Exception("Wrong backup level of the database detected in the job")
            log.info("Backup level confirmed: " + str(backuplevel))

            # modify database before TL2
            if not self.sqlhelper.modifydatabase.modify_db_for_inc(self.sqlhelper.dbname, list1, list2, list3):
                raise Exception("Databases couldn't be modified.")

            # Checking if databases are online
            if not self.sqlhelper.dbvalidate.is_db_online(self.sqlhelper.dbname, self.sqlhelper.noof_dbs):
                raise Exception("Databases are not online.")

            # write the database to file for comparison before TL
            if not self.sqlhelper.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                    self.sqlhelper.dbname,
                    list1,
                    list2,
                    list3,
                    'INCREMENTAL'
            ):
                raise Exception("Failed to write database to file.")

            # run a TL2
            job_id = self.sqlhelper.sql_backup('transaction_log')

            # check backup level for TL2
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id)
            if str(backuplevel) != "Transaction Log":
                raise Exception("Wrong backup level of the database detected in the job")
            log.info("Backup level confirmed: " + str(backuplevel))

            # get backup end time of TL2 from CS db
            tl3end = self.sqlhelper.get_sql_backup_end_time(job_id)
            log.info("Job End time - " + tl3end)

            # drop databases
            if not self.sqlhelper.dbinit.drop_databases(self.sqlhelper.dbname):
                log.error("Unable to drop the dataBase")

            # run restore in place job - based on TL2 time
            log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            if not self.sqlhelper.sql_restore(self.subclient.content, to_time=tl3end):
                raise Exception("Restore was not successful!")

            # Checking if databases are online
            if not self.sqlhelper.dbvalidate.is_db_online(self.sqlhelper.dbname, self.sqlhelper.noof_dbs):
                raise Exception("Databases are not online.")

            # write the restored database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, sqldump_file2),
                    self.sqlhelper.dbname,
                    list1,
                    list2,
                    list3,
                    'INCREMENTAL'
            ):
                raise Exception("Failed to write database to file.")

            # compare original and restored databases
            log.info("*" * 10 + " Validating content " + "*" * 10)
            if not self.sqlhelper.dbvalidate.db_compare(
                    os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                    os.path.join(self.sqlhelper.tcdir, sqldump_file2)
            ):
                raise Exception("Failed to compare both files.")

            log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""

        self.sqlhelper.sql_teardown()
