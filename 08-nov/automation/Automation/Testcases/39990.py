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

    get_metadata()  --  method to collect database information

    validate_data() --  validates the data in source and destination

    run()           --  Main function for test case execution

"""
import time
import ast
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of PostgreSQL backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Basic Acceptance Test of PostgreSQL backup and restore"
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.pgsql_db_object = None

    def setup(self):
        """setup function for this testcase"""

        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.postgres_db_password = self.postgres_helper_object.postgres_password
        self.pgsql_db_object = database_helper.PostgreSQL(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "postgres")

    def _run_backup(self, subclient, backup_type):
        """Initiates the backup job for the specified subclient

        Args:
            subclient            (obj)       -- Subclient object for which backup needs to be run

            backup_type          (str)       -- Type of backup (FULL/INCREMENTAL)

        Returns:
            job                              -- Object of Job class

        Raises:
            Exception:
                if unable to start the backup job

        """
        job = subclient.backup(backup_type)
        self.log.info(
            "Started %s backup with Job ID: %s", backup_type, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run %s backup job with error: %s" % (backup_type, job.delay_reason)
            )
        self.log.info("Successfully finished %s backup job", backup_type)

        return job

    def _run_restore(
            self, subclient, db_list, client_name, instance_name, table_level_restore=False):
        """Initiates the restore job for the specified subclient

        Args:
            subclient            (Obj)       -- Subclient object for which restore needs to be run

            db_list              (str)       -- Database list to restore

            client_name          (str)       -- Name of the client which subclient belongs to

            instance_name        (str)       -- Name of the instance which subclient belongs to

            table_level_restore  (bool)      -- Table level restore flag

                default:    False

        Returns:
            job                              -- Job object of the restore job

        Raises:
            Exception:
                if unable to start the restore job

        """
        self.log.debug("db_list = %s", db_list)
        self.log.debug("client_name = %s", client_name)
        self.log.debug("instance_name = %s", instance_name)
        backupset_name = subclient._backupset_object.backupset_name
        job = subclient.restore_postgres_server(
            db_list, client_name, instance_name, table_level_restore=table_level_restore)
        self.log.info(
            "Started %s Restore with Job ID: %s", backupset_name, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: %s" % job.delay_reason
            )

        self.log.info("Successfully finished %s restore job", backupset_name)
        self.postgres_helper_object.refresh()
        return job

    def get_metadata(self):
        """ method to collect database information

            Returns:
                dict        --      meta data info of database

            Raises:
                Exception:
                    if unable to get the database list

        """
        # Colecting Meta data after inc backup
        database_list = self.pgsql_db_object.get_db_list()
        if database_list is None:
            raise Exception(
                "Unable to get the database list."
            )
        # Get the subclient content Info before backup
        self.log.info(
            "Collect information of the subclient content")
        for database in ["postgres", "template0"]:
            if database in database_list:
                database_list.remove(database)
        return self.postgres_helper_object.generate_db_info(
            database_list,
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password)

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
        else:
            self.log.info(
                "###Database information validation passed successfully..!!###")

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
            postgres_data_population_size = self.tcinputs['TestDataSize']
            if isinstance(postgres_data_population_size, str):
                postgres_data_population_size = ast.literal_eval(postgres_data_population_size)
            num_of_databases = postgres_data_population_size[0]
            num_of_tables = postgres_data_population_size[1]
            num_of_rows = postgres_data_population_size[2]

            pgsql_server_user_name = self.instance._properties[
                'postGreSQLInstance']['SAUser']['userName']
            pgsql_server_port = self.instance._properties['postGreSQLInstance']['port']
            pgsql_server_hostname = self.client.client_hostname

            pgsql_bin_dir = self.instance._properties['postGreSQLInstance']['BinaryDirectory']
            self.log.info("Bin Directory: %s", pgsql_bin_dir)
            self.log.info("Postgres server Port: %s", pgsql_server_port)

            pgsql_data_dir = self.postgres_helper_object.get_postgres_data_dir(
                pgsql_bin_dir, self.postgres_db_password, pgsql_server_port)
            self.log.info("Postgres data directory: %s", pgsql_data_dir)

            ################# DumpBased Backup/Restore Operations ########################
            self.log.info(
                "#" * (10) + "  DumpBased Backup/Restore Operations  " + "#" * (10))
            backup_set = self.instance.backupsets.get("dumpbasedbackupset")
            subclient_dict = (backup_set.subclients._subclients)
            subclient = backup_set.subclients.get("default")
            subclient_list = list(subclient_dict.keys())

            db_prefix = "auto_full_dmp"
            self.log.info("Generating Test Data")
            self.postgres_helper_object.generate_test_data(
                pgsql_server_hostname,
                num_of_databases,
                num_of_tables,
                num_of_rows,
                pgsql_server_port,
                pgsql_server_user_name,
                self.postgres_db_password,
                True,
                db_prefix)
            self.log.info("Test Data Generated successfully")

            db_list_before_backup = None
            # Get Subclient content
            # check if subclient exists or not if not default subclient
            self.log.info("Collecting DB List")
            if subclient.subclient_name.lower() == "default":
                db_list_before_backup = self.pgsql_db_object.get_db_list()
                if db_list_before_backup is None:
                    self.log.error(
                        "Unable to get the database list.Cleaning up test data.")
                    return 1
                # Get list of all the subclients content and exclude them from total list
                # of Databases
                self.log.debug(db_list_before_backup)
                all_other_sub_clients_contents = list()
                for sub_client in subclient_list:
                    if sub_client.lower() != backup_set.subclients.default_subclient.lower():
                        self.log.info("Subclient is not default subclient: %s", sub_client)
                        sub_client_new = backup_set.subclients.get(sub_client)
                        self.log.info("Contents of subclients: %s", sub_client_new.content)
                        sub_client_db_list = sub_client_new.content
                        self.log.info(
                            "Database list of %s Subclient is %s", sub_client, sub_client_db_list)
                        for database in sub_client_db_list:
                            all_other_sub_clients_contents.append(
                                database.lstrip("/"))
                for db_name in all_other_sub_clients_contents:
                    if db_name in db_list_before_backup:
                        db_list_before_backup.remove(db_name)
            else:
                if self.subclient.subclient_name not in subclient_list:
                    raise Exception(
                        "{0} SubClient Does't exist".format(
                            self.subclient.subclient_name))

                sub_client_content = self.subclient.content
                db_list = []
                for i in sub_client_content:
                    db_list.append(
                        sub_client_content[i]['postgreSQLContent']['databaseName'])

                db_list_before_backup = db_list

                self.log.info(subclient.content)
                self.log.info("Subclient Contents:")
                self.log.info(db_list)
                db_list_before_backup = self.postgres_helper_object.strip_slash_char(
                    db_list_before_backup)

            before_full_backup_db_list = self.get_metadata()

            ###################### Running Full Backup ##############################
            self.log.info(
                "#" * (10) + "  Running Dumpbased Full Backup  " + "#" * (10))
            self._run_backup(subclient, "FULL")

            # appending "/" to dbnames for dumpbased restore
            for i in ["postgres", "template0"]:
                if i in db_list_before_backup:
                    db_list_before_backup.remove(i)
            db_list = ["/" + ele for ele in db_list_before_backup]
            time.sleep(float(10))
            self.log.info("Sleeping for 10 seconds")

            ##################### Running Table level restore #########################
            self.log.info("######### Performing table level restore #########")
            self.log.info("Deleting a table from database")
            self.postgres_helper_object.drop_table(
                "testtab_1",
                pgsql_server_hostname,
                pgsql_server_port,
                pgsql_server_user_name,
                self.postgres_db_password,
                "auto_full_dmp_testdb_0")
            self.log.info("Deleting function from database")
            self.postgres_helper_object.drop_function(
                "test_function_1", database="auto_full_dmp_testdb_0")
            self.log.info("### starting table level restore ###")
            self._run_restore(
                subclient,
                [
                    "/auto_full_dmp_testdb_0/public/testtab_1/",
                    "/auto_full_dmp_testdb_0/public/test_view_1/",
                    "/auto_full_dmp_testdb_0/public/test_function_1/"],
                self.client.client_name,
                self.instance.instance_name,
                table_level_restore=True)

            after_restore_db_info = self.get_metadata()

            self.validate_data(before_full_backup_db_list, after_restore_db_info)

            self.log.info("Deleting Automation Created databases")
            tc_name = "auto"
            self.postgres_helper_object.cleanup_tc_db(
                pgsql_server_hostname,
                pgsql_server_port,
                pgsql_server_user_name,
                self.postgres_db_password,
                tc_name)

            ####################### Running restore ###################################
            self.log.info(
                "#" * (10) + "  Running Dumpbased Restore  " + "#" * (10))
            self.log.info("Database list to restore:%s", db_list)
            self._run_restore(
                subclient, db_list, self.client.client_name, self.instance.instance_name)

            after_restore_db_info = self.get_metadata()
            self.validate_data(before_full_backup_db_list, after_restore_db_info)

            # ########################## FS Backup/Restore Operation #################

            # Running FS Backup FULL
            self.log.info(
                "#" * (10) + "  Running FSBased Full Backup  " + "#" * (10))
            backup_set = self.instance.backupsets.get("fsbasedbackupset")
            subclient_dict = (backup_set.subclients._get_subclients())
            subclient = backup_set.subclients.get("default")
            subclient_list = list(subclient_dict.keys())

            self._run_backup(subclient, "FULL")

            # Modifications to DB before incremental
            db_prefix = "auto_incr_fs"
            self.postgres_helper_object.generate_test_data(
                pgsql_server_hostname,
                num_of_databases,
                num_of_tables,
                num_of_rows,
                pgsql_server_port,
                pgsql_server_user_name,
                self.postgres_db_password,
                True,
                db_prefix)
            self.log.info("Test Data Generated successfully")

            before_full_backup_db_list = self.get_metadata()

            # Running FS Backup Log
            self.log.info(
                "#" * (10) + "  Running FSBased Incremental Backup  " + "#" * (10))
            self._run_backup(subclient, "INCREMENTAL")

            time.sleep(float(10))
            self.log.info("Sleeping for 10 seconds")

            ## cleaning up data and wal directories and
            ##stopping postgres server before the restore
            self.postgres_helper_object.cleanup_database_directories()

            # Running FS Restore
            self.log.info(
                "#" * (10) + "  Running FSBased Restore  " + "#" * (10))
            db_list = ["/data"]
            self._run_restore(
                subclient, db_list, self.client.client_name, self.instance.instance_name)

            db_list = ["/" + ele for ele in db_list_before_backup]

            self.pgsql_db_object.reconnect()
            after_restore_db_info = self.get_metadata()

            self.validate_data(before_full_backup_db_list, after_restore_db_info)

            time.sleep(float(10))
            self.log.info("sleeping for 10 seconds")

            self.log.info("Deleting Automation Created databases")
            tc_name = "auto"
            self.postgres_helper_object.cleanup_tc_db(
                pgsql_server_hostname,
                pgsql_server_port,
                pgsql_server_user_name,
                self.postgres_db_password,
                tc_name)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
