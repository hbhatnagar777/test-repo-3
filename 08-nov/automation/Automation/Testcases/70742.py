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
              "70742": {
                        "ClientName": "",
                        "AgentName" : "",
                        "InstanceName" : "",
                        "LibraryName": "",
                        "MediaAgentName": "",
                        "DirectoryPathOnLUN": "",
                        "SnapEngineName": "",
                        "SQLServerName" : "",
                        "SQLServerUser" : "",
                        "SQLServerPassword" : "",
                        "OOPRestorePath": ""
                    }
            }

"""
import os
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.constants import SnapShotEngineNames
from Application.SQL import sqlconstants
from Application.SQL.sqlhelper import SQLHelper


class TestCase(CVTestCase):
    """Class for executing SQL snap backup, OOP restore and hardware snap revert"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL: Snap backup, OOP Restore and H/W Revert"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MSSQL
        self.show_to_user = False
        self.sqlhelper = None
        self.subclient = None
        self.tcinputs = {
            "LibraryName": None,
            "MediaAgentName": None,
            "SnapEngineName": None,
            "SQLServerUser": None,
            "SQLServerPassword": None,
            "DirectoryPathOnLUN": None,
            "OOPRestorePath": None
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

    @test_step
    def create_snap_subclient(self):
        """Creates a SQL snap subclient"""
        self.sqlhelper.sql_setup(
            noof_dbs=1,
            noof_ffg_db=1,
            db_path=self.tcinputs['DirectoryPathOnLUN'],
            snap_setup=True,
            library_name=self.tcinputs['LibraryName'],
            media_agent=self.tcinputs['MediaAgentName']
        )

        self.subclient = self.sqlhelper.subclient

        if not SnapShotEngineNames(self.tcinputs["SnapEngineName"]):
            self.log.info("Snap Engine Name [{0}] is invalid. Please enter correct Snap Engine Name"
                          .format(self.tcinputs["SnapEngineName"]))

        self.log.info('Enabling Intelli-Snap for the created subclient %s', self.subclient.name)
        self.subclient.enable_intelli_snap(self.tcinputs["SnapEngineName"])

    @test_step
    def run_snap_backup(self, backup_type):
        """Runs the hardware snap backup"""
        backup_jobid = self.sqlhelper.sql_backup(backup_type)
        self.__confirm_backup_type(backup_jobid, 'full')
        return backup_jobid

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
    def dump_db_to_file(self, file_name, dbname, list1, list2, list3):
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

    def _delete_db_before_restore(self):
        """Deletes dbs from SQL Instance before running restore job"""
        self.log.info("*" * 10 + " Deleting dbs before running restore " + "*" * 10)
        if not self.sqlhelper.dbinit.drop_databases(self.sqlhelper.dbname):
            self.log.error("Unable to drop the database")

    @test_step
    def validate_restore(self, dump_file1, dump_file2):
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

    @test_step
    def run_oop_restore(self, file_path):
        """Runs Out-of-Place SQL Restore
        Args:
            file_path   (str)       :   File path for destination DB
        """
        database_name_list = []
        for content in self.sqlhelper.subcontent:
            database_name_dict = {
                'database_names': {
                    sqlconstants.DATABASE_ORIG_NAME: content,
                    sqlconstants.DATABASE_NEW_NAME: content
                }
            }

            database_name_list.append(database_name_dict)

        restore_path_list = self.sqlhelper.get_file_list_restore(database_name_list, file_path)

        self._delete_db_before_restore()

        self.log.info("*" * 10 + " Running Out-of-place restore " + "*" * 10)
        if not self.sqlhelper.sql_restore(self.subclient.content, restore_path=restore_path_list):
            raise CVTestStepFailure("Restore was not successful. Please check logs")

    @test_step
    def do_hardware_revert(self, bkp_job_id):
        """Performs and verifies the hardware revert
        Args:
            bkp_job_id      :       Job ID of the backup job to revert to
        """
        self.log.info("Creating a file on the Snap drive to verify if revert was a success")
        snap_machine = self.sqlhelper.sqlautomation.sqlmachine
        filepath = snap_machine.join_path(self.tcinputs['DirectoryPathOnLUN'], 'RevertTest.txt')
        # Check if file already exists. If yes, delete it
        if snap_machine.check_file_exists(filepath):
            snap_machine.delete_file(filepath)
        self.sqlhelper.sqlautomation.sqlmachine.create_file(filepath, 'Test file for revert')
        self.log.info("Performing hardware revert now")
        revert_to_time = self.sqlhelper.get_sql_backup_end_time(bkp_job_id, 'datestringformat')
        if not self.sqlhelper.sql_restore(self.subclient.content, to_time=revert_to_time, hardware_revert=True):
            raise CVTestStepFailure("Hardware revert was not successful. Please check logs")
        self.log.info("The restore job with revert was successful!! The file created above should not exist now")
        if snap_machine.check_file_exists(filepath):
            raise CVTestStepFailure("The file still exists. So Hardware revert was not successful. Please check logs")
        self.log.info("The file does not exist. Yaay!!")

    def run(self):
        """ Main function for test case execution """
        try:
            sqldump_file1 = "before_backup_full.txt"
            sqldump_file2 = "after_restore.txt"

            self.log.info("Started executing {0} testcase".format(self.id))

            self.create_snap_subclient()
            job_id = self.run_snap_backup('Full')

            # modify database before next backup
            self.modify_db()

            # submit a diff backup here. JM should convert it and run the job as full
            job_id = self.run_snap_backup('Differential')

            self.sqlhelper.run_backup_copy()

            # write the original database to file for comparison
            list1, list2, list3 = self.get_random_dbnames_and_filegroups()
            self.dump_db_to_file(sqldump_file1, self.sqlhelper.dbname, list1, list2, list3)

            self.run_oop_restore(self.tcinputs["OOPRestorePath"])
            # write the restored database to file for comparison
            self.dump_db_to_file(sqldump_file2, self.sqlhelper.dbname, list1, list2, list3)

            # compare original and restored databases
            self.validate_restore(sqldump_file1, sqldump_file2)

            self.do_hardware_revert(job_id)

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""
        self.sqlhelper.sql_teardown()


