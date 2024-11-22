# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  Initializes test case class object

    setup()             --  setup function for this testcase

    run_backup()        --  method to populate data and run
    backup job

    data_validation()   --  method to collect database information
    and validate the data

    tear_down()         --  tear down function to delete automation
    generated data

    run()               --  Main function for test case execution

"""
import time
import ast
from AutomationUtils import constants, idautils, database_helper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import machine
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.dbhelper import DbHelper

class TestCase(CVTestCase):
    """Class for executing Synthfull backup in loop test of PostgreSQL
    BLOCK level backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Synthfull backup in a loop and verify restores from each"
        self.tcinputs = {
            'TestDataSize': None,
            'PortForClone': None
        }
        self.postgres_data_population_size = None
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.dbhelper_object = None
        self.pgsql_db_object = None

    def setup(self):
        """setup function for this testcase"""
        if isinstance(self.tcinputs['TestDataSize'], str):
            self.tcinputs['TestDataSize'] = ast.literal_eval(self.tcinputs['TestDataSize'])
        self.postgres_data_population_size = self.tcinputs['TestDataSize']

        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.postgres_db_password = self.postgres_helper_object.postgres_password
        self.dbhelper_object = DbHelper(self.commcell)
        self.pgsql_db_object = database_helper.PostgreSQL(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "postgres")

    def run_backup(
            self,
            db_name_suffix=None,
            backup_level="FULL"):
        """ method to populate data and run backup job

            Args:
                db_name_suffix      (str)  --  suffix to the database
                being created

                backup_level        (str)  --  backup level

                    Accepted Values: FULL/INCREMENTAL

                    default: "FULL"

            Returns:

                job                 (obj)  --  job object

            Raises:
                Exception:

                    if unable to run backup job

        """
        self.log.info("Adding data before running %s backup", backup_level)
        self.log.info("Generating Test Data")
        num_of_databases = 1
        num_of_tables = 5
        num_of_rows = 100
        database_name = "auto_snap_inc{0}".format(db_name_suffix)
        if backup_level.lower() == "full":
            num_of_databases = self.postgres_data_population_size[0]
            num_of_tables = self.postgres_data_population_size[1]
            num_of_rows = self.postgres_data_population_size[2]
            database_name = "auto_snap"
        self.postgres_helper_object.generate_test_data(
            self.client.client_hostname,
            num_of_databases,
            num_of_tables,
            num_of_rows,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            True,
            database_name)

        ### run incremental backup
        self.log.info("###Starting %s backup job###", backup_level)
        if backup_level.lower() == "full":
            job = self.dbhelper_object.run_backup(
                self.subclient,
                "FULL")
        else:
            job = self.dbhelper_object.run_backup(
                self.subclient,
                "Incremental",
                inc_with_data=True)
        ###### Wait for log backup to complete
        job_log = self.dbhelper_object.get_snap_log_backup_job(job.job_id)
        self.log.info(
            "Log backup job with ID:%s is now completed",
            job_log.job_id)
        if not job_log.wait_for_completion():
            raise Exception(
                "Failed to run log backup job with error: {0}".format(
                    job_log.delay_reason
                )
            )
        return job

    def data_validation(self, database_port, db_info_to_compare):
        """ method to collect database information and validate the data

            Args:
                database_port       (str)  --  port number of database

                db_info_to_compare  (dict) --  database information to compare against
                the information fetched after restore

            Raises:
                Exception:

                    if unable to get database list

                    if database validation is failed

        """
        ignore_db_list = ["postgres", "template0"]
        db_list_after_restore = self.pgsql_db_object.get_db_list()
        if db_list_after_restore is None:
            raise Exception(
                "Unable to get the database list."
            )
        self.log.info(
            "Collect information of the subclient content after restore")
        for database in ignore_db_list:
            if database in db_list_after_restore:
                db_list_after_restore.remove(database)

        self.log.info("Collecting the DB info from cloned database")

        db_info_after_restore = self.postgres_helper_object.generate_db_info(
            db_list_after_restore,
            self.client.client_hostname,
            database_port,
            self.instance.postgres_server_user_name,
            self.postgres_db_password)

        # validation using meta data

        self.log.info(("Validating the database information collected before"
                       "SNAP Incremental 2nd Backup and after clone Restore"))
        if not self.postgres_helper_object.validate_db_info(
                db_info_to_compare, db_info_after_restore):
            raise Exception(
                "Database information validation failed."
            )
        else:
            self.log.info(
                "Database information validation passed successfully")

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
            self.log.info("Started executing %s testcase", self.id)
            self.log.info("Checking if the intelliSnap is enabled on subclient or not")
            if not self.subclient.is_intelli_snap_enabled:
                raise Exception("Intellisnap is not enabled for subclient")
            self.log.info("IntelliSnap is enabled on subclient")

            self.log.info("Checking if the Block level backup is enabled on subclient or not")
            if not self.subclient.is_blocklevel_backup_enabled:
                raise Exception("Block level backup is not enabled for subclient")
            self.log.info("Block level backup is enabled on subclient")

            ignore_db_list = ["postgres", "template0"]
            postgres_data_directory = self.postgres_helper_object.get_postgres_data_dir(
                self.instance.postgres_bin_directory,
                self.postgres_db_password,
                self.instance.postgres_server_port_number)

            ########################## SNAP Backup/Restore Operation ##########
            self.log.info("##### SNAP Backup/Restore Operations #####")

            self.run_backup()

            db_info_before_inc_backup = None

            ###### run 2 incremental and synth full in loop

            for iteration in range(0, 3):
                incremental_job = None
                for incremental_job in range(1, 3):
                    incremental_job = self.run_backup(
                        "_{0}_{1}".format(incremental_job, iteration),
                        backup_level="INCREMENTAL")

                # Colecting Meta data after inc backup
                db_list_before_backup = self.pgsql_db_object.get_db_list()
                if db_list_before_backup is None:
                    raise Exception(
                        "Unable to get the database list."
                    )
                # Get the subclient content Info before backup
                self.log.info(
                    "Collect information of the subclient content")
                for database in ignore_db_list:
                    if database in db_list_before_backup:
                        db_list_before_backup.remove(database)
                db_info_before_inc_backup = self.postgres_helper_object.generate_db_info(
                    db_list_before_backup,
                    self.client.client_hostname,
                    self.instance.postgres_server_port_number,
                    self.instance.postgres_server_user_name,
                    self.postgres_db_password)

                if "native" not in self.subclient.snapshot_engine_name.lower():
                    self.log.info("Snap engine is not native.")
                    ###### Run backup copy job #########
                    self.log.info(
                        "Running backup copy job for storage policy: %s",
                        self.subclient.storage_policy)
                    copy_precedence = self.dbhelper_object.run_backup_copy(
                        self.subclient.storage_policy)
                    self.log.info(
                        "Copy precedence of 'primary snap' copy is: %s",
                        copy_precedence)

                else:
                    self.log.info(
                        (
                            "Native Snap engine is being run. backup "
                            "copy job will run inline to snap backup"))
                    self.log.info("Getting the backup job ID of backup copy job")
                    job = self.dbhelper_object.get_backup_copy_job(incremental_job.job_id)
                    self.log.info("Job ID of backup copy Job is: %s", job.job_id)

                ############ run synthfull backup jobs ######
                self.log.info("Starting synthetic full backup.")
                synth_job = self.dbhelper_object.run_backup(self.subclient, "synthetic_full")
                self.log.info("Synthetic full backup %s is finished", synth_job.job_id)

                self.log.info(
                    ("Running data aging on storage policy:%s copy:primary to "
                     "make sure the restore is triggered from Synthfull backup"),
                    self.subclient.storage_policy)

                common_utils = idautils.CommonUtils(self.commcell)
                data_aging_job = common_utils.data_aging(
                    self.subclient.storage_policy, "primary", False)
                if not data_aging_job.wait_for_completion():
                    raise Exception(
                        "Failed to run data aging job with error: {0}".format(
                            data_aging_job.delay_reason
                        )
                    )
                self.log.info("Dataaging job run is:%s", data_aging_job.job_id)

                ############ Table level restore ############

                ######### Drop two tables from first database ########
                database_name = "auto_snap_inc_2_{0}_testdb_0".format(iteration)
                self.postgres_helper_object.drop_table(
                    "testtab_1",
                    self.client.client_hostname,
                    self.instance.postgres_server_port_number,
                    self.instance.postgres_server_user_name,
                    self.postgres_db_password,
                    database_name)
                self.postgres_helper_object.drop_view("test_view_0", database=database_name)

                self.log.info("Collecting meta data to validate data after restore.")
                table_info_before = self.postgres_helper_object.generate_db_info(
                    [database_name],
                    self.client.client_hostname,
                    self.instance.postgres_server_port_number,
                    self.instance.postgres_server_user_name,
                    self.postgres_db_password)
                self.postgres_helper_object.drop_table(
                    "testtab_0",
                    self.client.client_hostname,
                    self.instance.postgres_server_port_number,
                    self.instance.postgres_server_user_name,
                    self.postgres_db_password,
                    database_name)

                ######### start table level restore
                self.log.info("starting table level restore.")
                self.postgres_helper_object.run_restore(
                    ["/%s/public/testtab_0/" % (database_name)],
                    self.subclient,
                    media_agent=self.client.client_name,
                    table_level_restore=True)

                self.log.info("collecting meta data to validate.")
                table_info_after = self.postgres_helper_object.generate_db_info(
                    [database_name],
                    self.client.client_hostname,
                    self.instance.postgres_server_port_number,
                    self.instance.postgres_server_user_name,
                    self.postgres_db_password)

                return_code = self.postgres_helper_object.validate_db_info(
                    table_info_after, table_info_before)
                if not return_code:
                    raise Exception(
                        "Database info validation failed after table level restore."
                    )
                else:
                    self.log.info(
                        ("Database information validation passed "
                         "successfully for table level restore"))

                ########### verify clone restore #############
                storage_policy_object = self.commcell.storage_policies.get(
                    self.subclient.storage_policy)
                copy_precedence = storage_policy_object.get_copy_precedence("primary")
                self.log.info("starting clone restore")
                clone_options = {"stagingLocaion": "/tmp/53018",
                                 "forceCleanup": True,
                                 "port": str(self.tcinputs['PortForClone']),
                                 "libDirectory": self.instance.postgres_lib_directory,
                                 "isInstanceSelected": True,
                                 "reservationPeriodS": 3600,
                                 "user": self.instance.postgres_server_user_name,
                                 "binaryDirectory": self.instance.postgres_bin_directory
                                }
                self.log.info("Clone Options: %s", clone_options)
                job_id = self.postgres_helper_object.run_restore(
                    ["/data"],
                    self.subclient,
                    clone_env=True,
                    clone_options=clone_options,
                    copy_precedence=copy_precedence).job_id
                self.log.info("Adding listen address and restarting cloned servers for establishing connections")
                machine_object = machine.Machine(self.client)
                clone_config_file_path = machine_object.get_logs_for_job_from_file(
                    job_id, "POSTGRESBLKRESTORE.log", f".*mv.*/postgresql.conf6 .*/postgresql.conf").strip().split(" ")[
                    -1]
                clone_data_directory = clone_config_file_path.split('postgresql.conf')[0]
                machine_object.execute_command(f"echo \"listen_addresses='*'\" >> {clone_config_file_path}")
                machine_object.execute_command(
                    f"echo \"port={clone_options['port']}\" >> {clone_config_file_path}")
                self.postgres_helper_object.stop_postgres_server(self.instance.postgres_bin_directory, clone_data_directory)
                self.postgres_helper_object.start_postgres_server(self.instance.postgres_bin_directory, clone_data_directory)
                self.data_validation(
                    clone_options['port'],
                    db_info_before_inc_backup)

                ############ restore from primary copy ############
                self.log.info("Sleeping for 20 seconds before starting restore")
                time.sleep(20)

                # stopping postgres server and cleanup data/wal dirs before the restore
                self.postgres_helper_object.cleanup_database_directories()

                # Running FS Restore
                self.log.info(
                    "Restoring database from primary copy with precedence:%s",
                    copy_precedence)

                self.postgres_helper_object.run_restore(
                    ["/data"],
                    self.subclient,
                    copy_precedence=copy_precedence,
                    media_agent=self.client.client_name)

                del self.pgsql_db_object
                self.pgsql_db_object = database_helper.PostgreSQL(
                    self.client.client_hostname,
                    self.instance.postgres_server_port_number,
                    self.instance.postgres_server_user_name,
                    self.postgres_db_password,
                    "postgres")
                self.data_validation(
                    self.instance.postgres_server_port_number,
                    db_info_before_inc_backup)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
