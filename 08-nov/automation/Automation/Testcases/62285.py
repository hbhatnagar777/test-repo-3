# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initializes test case class object

    setup()         --  Setup function for this testcase

    _run_backup()   --  Initiates the backup job for the specified subclient

    _run_restore()  --  Initiates the restore job for the specified subclient

    wait_for_job()  --  waits for the job to complete

    get_metadata()  --  method to collect database information

    validate_data() --  validates the data in source and destination

    run()           --  Main function for test case execution

"""
import ast
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.dbhelper import DbHelper

class TestCase(CVTestCase):
    """Class for executing this testcase"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Cross machine restores after deleting ClientAccesscontrol table entries"
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.pgsql_db_object = None
        self.destination_client = None
        self.destination_instance = None
        self.destination_postgres_helper_object = None
        self.destination_postgres_db_password = None
        self.destination_pgsql_db_object = None
        self.db_helper = None
        self.cs_sql_user = get_config().SQL.Username
        self.cs_sql_password = get_config().SQL.Password
        if not (get_config().SQL.Username or get_config().SQL.Password):
            raise Exception("Please provide CSDB credentials in config file to run this testcase")

    def setup(self):
        """setup function for this testcase"""
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.postgres_db_password = self.postgres_helper_object.postgres_password
        self.pgsql_db_object = database_helper.PostgreSQL(
            self.client.client_hostname, self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,  self.postgres_db_password, "postgres")
        self.destination_client = self.commcell.clients.get(self.tcinputs['DestinationClient'])
        self.destination_instance = self.destination_client.agents.get(
            'postgresql').instances.get(self.tcinputs['DestinationInstance'])
        self.destination_postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.destination_client, self.destination_instance)
        self.destination_postgres_db_password = self.destination_postgres_helper_object.postgres_password
        self.destination_pgsql_db_object = database_helper.PostgreSQL(
            self.destination_client.client_hostname,
            self.destination_instance.postgres_server_port_number,
            self.destination_instance.postgres_server_user_name,
            self.destination_postgres_db_password, "postgres")
        self.db_helper = DbHelper(self.commcell)

    def _run_backup(self):
        """Initiates the backup job              -- Object of Job class

        Raises:
            Exception:
                if unable to start the backup job

        """
        postgres_data_population_size = self.tcinputs['TestDataSize']
        if isinstance(postgres_data_population_size, str):
            postgres_data_population_size = ast.literal_eval(postgres_data_population_size)
        num_of_databases = postgres_data_population_size[0]
        num_of_tables = postgres_data_population_size[1]
        num_of_rows = postgres_data_population_size[2]
        db_prefix = "auto_full_dmp"
        self.log.info("Generating Test Data")
        self.postgres_helper_object.generate_test_data(
            self.client.client_hostname, num_of_databases, num_of_tables, num_of_rows,
            self.instance.postgres_server_port_number, self.instance.postgres_server_user_name,
            self.postgres_db_password, True, db_prefix)
        self.log.info("Test Data Generated successfully")
        job = self.subclient.backup('FULL')
        self.wait_for_job(job)

    def _run_restore(self, db_list, table_level_restore=False):
        """Initiates the restore job for the specified subclient

        Args:
            db_list              (str)       -- Database list to restore

            table_level_restore  (bool)      -- Table level restore flag

                default:    False         -- Job object of the restore job

        Raises:
            Exception:
                if unable to start the restore job

        """
        self.log.info("Deleting entries from App_ClientAccessControl")
        self.db_helper.delete_client_access_control(self.client, self.destination_client)
        if table_level_restore:
            self.log.info("Deleting a table from database")
            self.destination_postgres_helper_object.drop_table(
                "testtab_1", self.destination_client.client_hostname,
                self.destination_instance.postgres_server_port_number,
                self.destination_instance.postgres_server_user_name,
                self.destination_postgres_db_password,
                "auto_full_dmp_testdb_0")
            self.log.info("Deleting function from database")
            self.destination_postgres_helper_object.drop_function(
                "test_function_1", database="auto_full_dmp_testdb_0")
        self.log.debug("db_list = %s", db_list)
        job = self.subclient.restore_postgres_server(
            db_list, self.destination_client.client_name, self.destination_instance.instance_name,
            table_level_restore=table_level_restore)
        self.wait_for_job(job)

    def wait_for_job(self, job):
        """ waits for the job to complete """
        self.log.info(
            "Started Job with Job ID: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: %s" % job.delay_reason
            )
        self.log.info("Successfully finished job")


    def get_metadata(self, destination=False):
        """ method to collect database information

            Args:
                destination (bool)  --  Boolean value to specify
                destination metadata collection

            Returns:
                dict        --      meta data info of database

            Raises:
                Exception:
                    if unable to get the database list

        """
        if destination:
            database_list = self.destination_pgsql_db_object.get_db_list()
        else:
            database_list = self.pgsql_db_object.get_db_list()
        database_list = [x for x in database_list if x not in self.postgres_helper_object.ignore_db_list]
        if destination:
            return self.destination_postgres_helper_object.generate_db_info(
                database_list, self.destination_client.client_hostname,
                self.destination_instance.postgres_server_port_number,
                self.destination_instance.postgres_server_user_name,
                self.destination_postgres_db_password)
        return self.postgres_helper_object.generate_db_info(
            database_list, self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name, self.postgres_db_password)

    def validate_data(self, db_info_source, db_info_destination):
        """validates the data in source and destination

            Args:
                db_info_source        (dict)  --  database information of source

                db_info_destination   (dict)  --  database information of destination

            Raises:
                Exception:

                    if database information validation failed

        """

        self.log.info("Validating the database information collected before \
            Incremental Backup and after volume level Restore")
        if not self.postgres_helper_object.validate_db_info(
                db_info_source, db_info_destination):
            raise Exception(
                "Database information validation failed.!!!"
            )
        self.log.info(
            "###Database information validation passed successfully..!!###")

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname, self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name, self.postgres_db_password, "auto")
        self.log.info("Deleting Automation Created databases")
        self.destination_postgres_helper_object.cleanup_tc_db(
            self.destination_client.client_hostname,
            self.destination_instance.postgres_server_port_number,
            self.destination_instance.postgres_server_user_name,
            self.destination_postgres_db_password,
            "auto")

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("  Running Dumpbased Full Backup  ")
            self._run_backup()

            self.log.info("Collecting DB List")
            db_list_before_backup = self.pgsql_db_object.get_db_list()
            before_full_backup_db_list = self.get_metadata()
            db_list_before_backup = [x for x in db_list_before_backup if x not in self.postgres_helper_object.ignore_db_list]
            db_list = ["/" + ele for ele in db_list_before_backup]
            self.log.info("  Running DB level Restore  ")
            self.log.info("Database list to restore:%s", db_list)
            self._run_restore(db_list)
            after_restore_db_info = self.get_metadata(destination=True)
            self.validate_data(before_full_backup_db_list, after_restore_db_info)
            self.log.info("######### Performing table level restore #########")
            self._run_restore(
                [
                    "/auto_full_dmp_testdb_0/public/testtab_1/",
                    "/auto_full_dmp_testdb_0/public/test_view_1/",
                    "/auto_full_dmp_testdb_0/public/test_function_1/"],
                table_level_restore=True)
            after_restore_db_info = self.get_metadata(destination=True)
            self.validate_data(before_full_backup_db_list, after_restore_db_info)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
