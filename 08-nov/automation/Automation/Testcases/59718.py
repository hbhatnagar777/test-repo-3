# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initializes test case class object

    setup()         --  Setup function for this testcase

    run_backup()   --  Initiates the backup job for the specified subclient

    prepare_table_restore() --  method to perform pre-reqs for table restore

    run_restore_validate()  --  Initiates the restore job for the specified
    subclient and validates data

    run()           --  Main function for test case execution

"""
import ast
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Database.PostgreSQL.PostgresUtils import pgsqlhelper


class TestCase(CVTestCase):
    """Class for executing Index reconstruction case for PgSQL V1 clients"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Index reconstruction case for PgSQL V1 client"
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.db_helper = None
        self.postgres_data_population_size = None
        self.pgsql_data_dir = None

    def setup(self):
        """setup function for this testcase"""
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        if self.postgres_helper_object.is_index_v2_postgres:
            raise Exception("This testcase requires the client to be Indexing V1")
        self.postgres_db_password = self.postgres_helper_object.postgres_password
        self.postgres_data_population_size = self.tcinputs['TestDataSize']
        if isinstance(self.postgres_data_population_size, str):
            self.postgres_data_population_size = ast.literal_eval(
                self.postgres_data_population_size)
        self.pgsql_data_dir = self.postgres_helper_object.get_postgres_data_dir(
            self.instance.postgres_bin_directory,
            self.postgres_db_password,
            self.instance.postgres_server_port_number)
        self.db_helper = DbHelper(self.commcell)

    def run_backup(
            self, backup_level="FULL", backupset="fsbasedbackupset", db_prefix="auto"):
        """Initiates the backup job for the specified subclient

        Args:
            backup_level    (str)   -- Type of backup (FULL/INCREMENTAL)

            backupset       (str)   -- backupset name

            db_prefix       (str)   -- db prefix to string to create database

        Returns:
            job         -- Object of Job class
            meta_data   -- metadata collected after backup
            subclient   -- subclient object
            db_list     -- database list created for backup

        Raises:
            Exception:
                if unable to start the backup job

        """
        self.log.info("Generating Test Data")
        num_of_databases = self.postgres_data_population_size[0]
        num_of_tables = self.postgres_data_population_size[1]
        num_of_rows = self.postgres_data_population_size[2]
        db_list = self.postgres_helper_object.generate_test_data(
            self.client.client_hostname,
            num_of_databases,
            num_of_tables,
            num_of_rows,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            True,
            db_prefix)
        backup_set = self.instance.backupsets.get(backupset)
        subclient = backup_set.subclients.get("default")
        self.log.info("Running backup for backupset:%s", backupset)
        job = subclient.backup(backup_level)
        meta_data = self.postgres_helper_object.get_metadata()
        self.log.info(
            "Started %s backup with Job ID: %s", backup_level, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run %s backup job with error: %s" % (backup_level, job.delay_reason)
            )
        self.log.info("Successfully finished %s backup job", backup_level)
        self.log.info("Performing index delete operation after backup")
        return meta_data, subclient, db_list

    def prepare_table_restore(self):
        """ method to perform pre-reqs for table restore"""
        self.log.info("Deleting a table from database")
        self.postgres_helper_object.drop_table(
            "testtab_1",
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "auto_dump_testdb_0")
        self.log.info("Deleting function from database")
        self.postgres_helper_object.drop_function(
            "test_function_1", database="auto_dump_testdb_0")

    def run_restore_validate(
            self, subclient, db_list, meta_data, table_level_restore=False):
        """Initiates the restore job for the specified subclient and validates data

        Args:
            subclient            (Obj)       -- Subclient object for which restore needs to be run

            db_list              (str)       -- Database list to restore

            meta_data            (dict)      -- Dictionary containing meta data info before backup

            table_level_restore  (bool)      -- Table level restore flag

                default:    False

        Raises:
            Exception:
                if unable to start the restore job

        """
        self.db_helper.delete_v1_index_restart_service(subclient)
        is_dump_based = "dump" in subclient._backupset_object.backupset_name
        if is_dump_based:
            if not table_level_restore:
                self.postgres_helper_object.cleanup_test_data(db_list)
                db_list = ["/" + ele for ele in db_list]
            else:
                db_list = [
                    "/auto_dump_testdb_0/public/testtab_1/",
                    "/auto_dump_testdb_0/public/test_view_1/",
                    "/auto_dump_testdb_0/public/test_function_1/"]
                self.prepare_table_restore()
        else:
            self.postgres_helper_object.cleanup_database_directories()
            db_list = ["/data"]
        self.postgres_helper_object.run_restore(
            db_list, subclient,
            is_dump_based=is_dump_based, table_level_restore=table_level_restore)
        meta_data_after_restore = self.postgres_helper_object.get_metadata()
        self.postgres_helper_object.validate_db_info(meta_data, meta_data_after_restore)

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "auto")

    def run(self):
        """Main function for test case execution"""

        try:
            meta_data, subclient, db_list = self.run_backup(
                backupset="dumpbasedbackupset", db_prefix="auto_dump")
            self.run_restore_validate(subclient, db_list, meta_data, True)
            self.run_restore_validate(subclient, db_list, meta_data)

            meta_data, subclient, db_list = self.run_backup(
                db_prefix="auto_fs_full")
            self.run_restore_validate(subclient, db_list, meta_data)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
