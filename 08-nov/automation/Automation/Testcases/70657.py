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
import Application.SQL.sqlconstants as sqlconstants
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from Application.SQL.sqlhelper import SQLHelper
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of SQL Server restore with NORECOVERY test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL - Data Recovery - Restore with NORECOVERY"

        self.sqlhelper = None
        self.sqlmachine = None

        self.tcinputs = {
            "SQLServerUser": None,
            "SQLServerPassword": None
        }

    def setup(self):
        """ Method to setup test variables """
        clientname = self.client.client_name
        instancename = self.instance.instance_name
        sqluser = self.tcinputs["SQLServerUser"]
        sqlpass = self.tcinputs["SQLServerPassword"]

        self.sqlmachine = Machine(self.client)
        self.sqlhelper = SQLHelper(self, clientname, instancename, sqluser, sqlpass)

        self.sqlhelper.sql_setup(noof_dbs=1)
        self.subclient = self.sqlhelper.subclient

    def get_backup_type(self, job_id, backup_type):
        """Method to confirm the type of backup job run"""

        backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id, multidb=False)
        if str(backuplevel).lower() != backup_type.lower():
            raise Exception("Wrong backup level of the database detected in the job")
        else:
            self.log.info("Backup level confirmed: " + str(backuplevel))

    def run(self):
        """Main function for test case execution"""

        try:
            sqldump_file1 = "before_backup_inc.txt"
            sqldump_file2 = "after_restore.txt"

            self.log.info("Started executing {0} testcase".format(self.id))

            # get table shuffled list
            returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                100, self.sqlhelper.noof_dbs, self.sqlhelper.noof_ffg_db, self.sqlhelper.noof_tables_ffg
            )
            if not returnstring:
                raise Exception("Error in while generating the random number.")

            # run a Full backup
            job_id = self.sqlhelper.sql_backup('full')

            # check backup level should be full
            self.get_backup_type(job_id, 'full')

            # modify database before TL
            if not self.sqlhelper.modifydatabase.modify_db_for_inc(self.sqlhelper.dbname, list1, list2, list3):
                raise Exception("Databases couldn't be modified.")

            # run a TL backup
            job_id = self.sqlhelper.sql_backup('transaction_log')

            # check backup level for TL
            self.get_backup_type(job_id, 'transaction log')

            # Checking if databases are online
            if not self.sqlhelper.dbvalidate.is_db_online(self.sqlhelper.dbname, self.sqlhelper.noof_dbs):
                raise Exception("Databases are not online.")
           
            # write the database to file for comparison after TL
            if not self.sqlhelper.dbvalidate.dump_db_to_file(os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                                                             self.sqlhelper.dbname, list1, list2, list3, 'INCREMENTAL'):
                raise Exception("Failed to write database to file.")

            # get backup end time of TL3 from CS db
            tlend = self.sqlhelper.get_sql_backup_end_time(job_id, timeformat="datestringformat")
            self.log.info("Job End time - " + tlend)
            
            # drop databases
            if not self.sqlhelper.dbinit.drop_databases(self.sqlhelper.dbname):
                self.log.error("Unable to drop the dataBase")            

            # run restore in place job - based on TL time
            self.log.info("*" * 10 + " Run Restore in place with NORECOVERY" + "*" * 10)
            if not self.sqlhelper.sql_restore(
                    self.subclient.content,
                    to_time=tlend,
                    sql_recover_type=sqlconstants.STATE_NORECOVER
            ):
                raise Exception("Restore was not successful!")

            # Checking if databases are online
            if not self.sqlhelper.dbvalidate.get_database_state(self.sqlhelper.dbname + str(1)) == 'RESTORING':
                raise Exception("Databases is not in restoring state.")

            # run restore with recovery only
            self.log.info("*" * 10 + " Run Restore in place with RECOVERY ONLY" + "*" * 10)
            if not self.sqlhelper.sql_restore(
                    self.subclient.content,
                    to_time=tlend,
                    sql_recover_type=sqlconstants.STATE_RECOVER,
                    sql_restore_type=sqlconstants.RECOVER_ONLY
            ):
                raise Exception("Restore was not successful!")

            # write the restored database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(os.path.join(self.sqlhelper.tcdir, sqldump_file2),
                                                             self.sqlhelper.dbname, list1, list2, list3, 'INCREMENTAL'):
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
