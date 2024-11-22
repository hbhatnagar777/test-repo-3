# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                              --  Initialize TestCase class

    setup()                                 --  Setup method for test case


    run()                                   --  Run function of this test case

Input Example :

    "testCases": {
              "70794": {
                        "ClientName": "",
                        "AgentName" : "",
                        "InstanceName" : "",
                        "LibraryName": "",
                        "MediaAgentName": "",
                        "SQLServerName" : "",
                        "SQLServerUser" : "",
                        "SQLServerPassword" : ""
                    }
            }

"""
import os
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Application.SQL.sqlhelper import SQLHelper


class TestCase(CVTestCase):
    """Class for executing SQL block backups and restores"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL: Block backups and restores"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MSSQL
        self.show_to_user = False
        self.sqlhelper = None
        self.subclient = None
        self.tcinputs = {
            "LibraryName": None,
            "MediaAgentName": None,
            "SQLServerUser": None,
            "SQLServerPassword": None,
        }

    def setup(self):
        """Setup function for the testcase"""
        self.sqlhelper = SQLHelper(
            self,
            self.client.client_name,
            self.instance.instance_name,
            self.tcinputs['SQLServerUser'],
            self.tcinputs['SQLServerPassword'],
        )

    def __confirm_backup_type(self, job_id, backup_type):
        """Method to confirm the type of backup job run"""

        backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id, multidb=False)
        if str(backuplevel).lower() != backup_type.lower():
            raise Exception("Wrong backup level of the database detected in the job")
        else:
            self.log.info("Backup level confirmed: " + str(backuplevel))

    def __dump_db_to_file(self, file_name, dbname, list1, list2, list3):
        """Dumps db to file for comparison"""
        if not self.sqlhelper.dbvalidate.dump_db_to_file(
                os.path.join(self.sqlhelper.tcdir, file_name),
                dbname,
                list1,
                list2,
                list3,
                'FULL'
        ):
            raise CVTestStepFailure("Failed to write database to file.")

    def __delete_dbs_before_restore(self):
        """Deletes dbs from SQL Instance before running restore job"""
        self.log.info("*" * 10 + " Deleting dbs before running restore " + "*" * 10)
        if not self.sqlhelper.dbinit.drop_databases(self.sqlhelper.dbname):
            self.log.error("Unable to drop the database")

    def __validate_restore(self, dump_file1, dump_file2):
        """Validates the restore job by comparing source and restored dumped db files
        Args:
            dump_file1      (str)       :       Dump file of source db
            dump_file2      (str)       :       Dump file of restored db
        """
        self.log.info("*" * 10 + " Validating content " + "*" * 10)
        if not self.sqlhelper.dbvalidate.db_compare(os.path.join(self.sqlhelper.tcdir, dump_file1),
                                                    os.path.join(self.sqlhelper.tcdir, dump_file2)):
            raise CVTestStepFailure("Failed to compare both files.")
        self.log.info("*" * 10 + " Validation successful " + "*" * 10)

    def get_random_dbnames_and_filegroups(self):
        """Returns the values required to dump the db"""
        # get table shuffled list
        returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
            100,
            self.sqlhelper.noof_dbs,
            self.sqlhelper.noof_ffg_db,
            self.sqlhelper.noof_tables_ffg
        )
        if not returnstring:
            raise CVTestStepFailure("Error in while generating the random number.")
        return list1, list2, list3

    @test_step
    def create_block_subclient(self):
        """Creates a SQL block subclient"""
        self.sqlhelper.sql_setup(
            library_name=self.tcinputs['LibraryName'],
            media_agent=self.tcinputs['MediaAgentName']
        )

        self.subclient = self.sqlhelper.subclient

        self.log.info('Enabling Block-Level backups for the created subclient %s', self.subclient.name)
        self.subclient.blocklevel_backup_option = True

    @test_step
    def run_block_backup(self, backup_type):
        """Runs the block backup"""
        backup_jobid = self.sqlhelper.sql_backup(backup_type)
        self.__confirm_backup_type(backup_jobid, 'full')

    @test_step
    def modify_db(self):
        """Add files to the DB"""
        returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
            100, self.sqlhelper.noof_dbs, self.sqlhelper.noof_ffg_db, self.sqlhelper.noof_tables_ffg
        )
        if not returnstring:
            raise CVTestStepFailure("Error in while generating the random number.")

        if not self.sqlhelper.modifydatabase.modify_db_for_inc(self.sqlhelper.dbname, list1, list2, list3):
            raise CVTestStepFailure("Databases couldn't be modified.")

    @test_step
    def run_restore(self):
        """Runs restore-in-place and validates the restored content"""
        sqldump_file1 = "before_backup_full.txt"
        sqldump_file2 = "after_restore.txt"

        # write the original database to file for comparison
        list1, list2, list3 = self.get_random_dbnames_and_filegroups()
        self.__dump_db_to_file(sqldump_file1, self.sqlhelper.dbname, list1, list2, list3)

        self.__delete_dbs_before_restore()
        self.log.info("*" * 10 + " Running restore in-place " + "*" * 10)
        if not self.sqlhelper.sql_restore(self.subclient.content):
            raise CVTestStepFailure("Restore was not successful!")

        self.__dump_db_to_file(sqldump_file2, self.sqlhelper.dbname, list1, list2, list3)

        self.__validate_restore(sqldump_file1, sqldump_file2)

    def run(self):
        """ Main function for test case execution """
        try:

            self.log.info("Started executing {0} testcase".format(self.id))

            self.create_block_subclient()
            self.run_block_backup('Full')

            # submit a diff backup here. JM should convert it and run the job as full
            self.log.info("!" * 10 + " This backup should be submitted as Full by JM since we do not "
                                     "support diff blocks backups. " + "!" * 10)
            self.run_block_backup('Differential')

            self.run_restore()

            # submit a log backup here. This should convert to Full since restore was done before
            self.log.info("!" * 10 + "This log backup should be converted to full since we ran an in-place restore "
                                     "just now " + "!" * 10)
            self.run_block_backup('Transaction_Log')

            self.modify_db()
            backup_jobid = self.sqlhelper.sql_backup('Transaction_Log')
            self.__confirm_backup_type(backup_jobid, 'Transaction Log')

            self.run_restore()

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""
        self.sqlhelper.sql_teardown()


