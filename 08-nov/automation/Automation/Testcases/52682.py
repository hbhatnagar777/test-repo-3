# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
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
from Application.SQL.sqlhelper import SQLHelper
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of SQL Server backup and restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL - Data Protection - Differential Backup and Restore"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MSSQL
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True

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

            randomization = 100

            log.info("Started executing {0} testcase".format(self.id))

            self.sqlhelper.sql_setup()
            self.subclient = self.sqlhelper.subclient

            # get table shuffled list
            returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                randomization, self.sqlhelper.noof_dbs, self.sqlhelper.noof_ffg_db, self.sqlhelper.noof_tables_ffg
            )
            if not returnstring:
                raise Exception("Error in while generating the random number.")

            # run a full backup
            job_id = self.sqlhelper.sql_backup('Full')

            # check backup level for Full
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id, multidb=False)
            if str(backuplevel) != "Full":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                log.info("Backup level confirmed: " + str(backuplevel))
            
            # modify database before TL
            if not self.sqlhelper.modifydatabase.modify_db_for_inc(self.sqlhelper.dbname, list1, list2, list3):
                raise Exception("Database modification failed.")
            
            # run a TL backup
            job_id = self.sqlhelper.sql_backup('transaction_log')
            
            # check backup level for TL1
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id, multidb=False)
            if str(backuplevel) != "Transaction Log":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                log.info("Backup level confirmed: " + str(backuplevel))

            # get table shuffled list
            returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                randomization, self.sqlhelper.noof_dbs, self.sqlhelper.noof_ffg_db, self.sqlhelper.noof_tables_ffg
            )
            if not returnstring:
                raise Exception("Error in while generating the random number.")

            # modify database before TL2
            if not self.sqlhelper.modifydatabase.modify_db_for_inc(self.sqlhelper.dbname, list1, list2, list3, 2):
                raise Exception("Database modification failed.")
            
            # run a TL backup2
            job_id = self.sqlhelper.sql_backup('transaction_log')
            
            # check backup level for TL2
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id, multidb=False)
            if str(backuplevel) != "Transaction Log":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                log.info("Backup level confirmed: " + str(backuplevel))

            # modify database before DIFF
            if not self.sqlhelper.modifydatabase.modify_db_for_diff(self.sqlhelper.dbname, list1, list2, list3):
                raise Exception("Database modification failed.")

            # write the database to file for comparison before DIFF
            if not self.sqlhelper.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                    self.sqlhelper.dbname, list1, list2, list3, 'DIFFERENTIAL'
            ):
                raise Exception("Failed to write database to file.")

            # run a DIFF backup
            job_id = self.sqlhelper.sql_backup('differential')
            
            # check backup level for DIFF
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id, multidb=False)
            if str(backuplevel) != "Differential":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                log.info("Backup level confirmed: " + str(backuplevel))

            # get backup end time from CS db
            diffend = self.sqlhelper.get_sql_backup_end_time(job_id, timeformat="datestringformat")
            log.info("Job End time - " + diffend)
            
            if not self.sqlhelper.dbinit.kill_db_connections(self.sqlhelper.dbname, self.sqlhelper.noof_dbs, True):
                raise Exception("Unable to kill database connections")

            # run restore in place job - based on DIFF time
            log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            if not self.sqlhelper.sql_restore(self.subclient.content, to_time=diffend):
                raise Exception("Restore was not successful!")

            # Checking if databases are online
            if not self.sqlhelper.dbvalidate.is_db_online(self.sqlhelper.dbname, self.sqlhelper.noof_dbs):
                raise Exception("Databases are not online.")

            # write the restored database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, sqldump_file2),
                    self.sqlhelper.dbname, list1, list2, list3, 'DIFFERENTIAL'
            ):
                raise Exception("Failed to write database to file.")

            # compare original and restored databases
            log.info("*" * 10 + " Validating content " + "*" * 10)
            if not self.sqlhelper.dbvalidate.db_compare(os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                                                        os.path.join(self.sqlhelper.tcdir, sqldump_file2)):
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
