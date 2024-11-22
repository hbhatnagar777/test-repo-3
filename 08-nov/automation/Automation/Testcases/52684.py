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
from Application.SQL import sqlconstants
from Application.SQL.sqlhelper import SQLHelper
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of SQL Server backup and restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL Restore - Out of place"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MSSQL
        self.feature = self.features_list.DATARECOVERY
        self.show_to_user = True

        self.sqlhelper = None
        self.sqlmachine = None
        self.sqlhelper = None

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
        self.sqlhelper = SQLHelper(self, clientname, instancename, sqluser, sqlpass)
        self.sqlmachine = Machine(self.client)

        try:
            sqldump_file1 = "before_backup_full.txt"
            sqldump_file2 = "after_restore.txt"

            randomization = 100

            log.info("Started executing {0} testcase".format(self.id))

            self.sqlhelper.sql_setup()
            self.subclient = self.sqlhelper.subclient

            # get table shuffled list
            returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                randomization, self.sqlhelper.noof_dbs, self.sqlhelper.noof_ffg_db, self.sqlhelper.noof_tables_ffg)
            if not returnstring:
                raise Exception("Error in while generating the random number.")

            # write the original database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                                                             self.sqlhelper.dbname, list1, list2, list3, 'FULL'):
                raise Exception("Failed to write database to file.")

            # run a full backup
            if not self.sqlhelper.sql_backup('Full'):
                raise Exception("Failed to backup databases successfully.")

            # build dict with original database names and new names
            database_name_list = []
            for content in self.sqlhelper.subcontent:
                database_name_dict = {
                    'database_names': {
                        sqlconstants.DATABASE_ORIG_NAME: content,
                        sqlconstants.DATABASE_NEW_NAME: content
                    }
                }

                database_name_list.append(database_name_dict)

            restore_path_list = self.sqlhelper.get_file_list_restore(database_name_list, self.sqlhelper.tcdir)

            log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            if not self.sqlhelper.sql_restore(self.subclient.content, restore_path=restore_path_list):
                raise Exception("Restore was not successful!")

            # write the restored database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(os.path.join(self.sqlhelper.tcdir, sqldump_file2),
                                                             self.sqlhelper.dbname, list1, list2, list3, 'FULL'):
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