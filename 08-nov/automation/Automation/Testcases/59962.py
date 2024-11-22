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

    get_metadata()      --  method to collect database information

    backup_operations() --  populates data and runs FULL, Incremental
    and log backups

    run_restore()       --  starts the volume level restore job,
    waits for it to complete

    validate_data()     --  validates the data in source and destination

    tear_down()         --  tear down function to delete automation
    generated data

    run()               --  Main function for test case execution

"""
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils import idautils
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.dbhelper import DbHelper

class TestCase(CVTestCase):
    """Class for executing volume level restore index reconstruction for indexing V2 clients"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Volume level index reconstruction case for indexing V2 PostgreSQL clients"
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.pgsql_db_object = None
        self.dbhelper_object = None

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
        self.dbhelper_object = DbHelper(self.commcell)

    def get_metadata(self):
        """ method to collect database information

            Returns:
                dict        --      meta data info of database

            Raises:
                Exception:
                    if unable to get the database list

        """
        database_list = self.pgsql_db_object.get_db_list()
        if database_list is None:
            raise Exception(
                "Unable to get the database list."
            )
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

    def backup_operations(self, backup_type="FULL"):
        """Populates data and runs FULL, Incremental and log backups

            Args:
                backup_type         (str)   --  backup type

                    default:            FULL

                    accepted_values:    FULL/INCREMENTAL

            Returns:
                job                 (obj)   --  job object

        """
        self.log.info("Adding data before running %s backup", backup_type)
        self.log.info("Generating Test Data")
        database_prefix = "auto_snap"
        if "incremental" in backup_type.lower():
            database_prefix = "auto_snap_inc"
        self.postgres_helper_object.generate_test_data(
            self.client.client_hostname,
            3,
            5,
            250,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            True,
            database_prefix)

        self.log.info("###Starting %s backup job###", backup_type)
        inc_with_data = False
        if "incremental" in backup_type.lower():
            inc_with_data = True
        job = self.dbhelper_object.run_backup(
            self.subclient, backup_type, inc_with_data=inc_with_data)
        log_job = self.dbhelper_object.get_snap_log_backup_job(job.job_id)
        self.log.info("Log backup job with ID:%s is now completed", log_job.job_id)
        return job

    def run_restore(self, no_of_streams):
        """ starts the volume level restore job, waits for it to complete

            Args:
                no_of_streams       (int)   --  number of streams to be used for restore job

            Returns:
                job                 (obj)   --  job object

            Raises:
                Exception:

                    if failed to run restore job

        """
        self.dbhelper_object.delete_v2_index_restart_service(self.backupset)
        job = self.backupset.restore_postgres_server(
            ["/"],
            self.client.client_name,
            self.instance.instance_name,
            no_of_streams=no_of_streams,
            volume_level_restore=True)
        self.log.info(
            "Started Restore with Job ID: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: {0}".format(
                    job.delay_reason
                )
            )
        self.log.info(
            "Successfully finished restore job")
        return job

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
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "auto")


    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Checking if the client is indexing V2 enabled.")
            if not self.postgres_helper_object.is_index_v2_postgres:
                raise Exception("Indexing V2 is not enabled for the client.")
            self.log.info("Checking if the intelliSnap is enabled on subclient or not")
            if not self.subclient.is_intelli_snap_enabled:
                raise Exception("Intellisnap is not enabled for subclient")
            self.log.info("IntelliSnap is enabled on subclient")
            self.log.info("Checking if the Block level backup is enabled on subclient or not")
            if not self.subclient.is_blocklevel_backup_enabled:
                raise Exception("Block level backup is not enabled for subclient")
            self.log.info("Block level backup is enabled on subclient")

            ########### VOLUME LEVEL RESTORE OPERATIONS ##########
            self.log.info("##### VOLUME LEVEL RESTORE  OPERATIONS #####")
            full_job = self.backup_operations("FULL")
            self.backup_operations("INCREMENTAL")

            db_info_before_restore = self.get_metadata()

            if "native" not in self.subclient.snapshot_engine_name.lower():
                self.log.info("Snap engine is not native.")
                ###### Run backup copy job #########
                self.log.info(
                    "Running backup copy job for storage policy: %s",
                    self.subclient.storage_policy)
                self.log.info(
                    "Copy precedence of 'primary_snap' copy is: %s",
                    self.dbhelper_object.run_backup_copy(self.subclient.storage_policy))
            else:
                self.log.info(
                    ("Native Snap engine is being run. backup "
                     "copy job will run inline to snap backup"))
                self.log.info("Getting the backup job ID of backup copy job")
                job = self.dbhelper_object.get_backup_copy_job(full_job.job_id)
                self.log.info("Job ID of backup copy Job is: %s", job.job_id)

            self.log.info("Running Data aging as Index delete case being run")
            common_utils = idautils.CommonUtils(self.commcell)
            data_aging_job = common_utils.data_aging(
                self.subclient.storage_policy, "primary", False)
            self.log.info("Dataaging job run is:%s", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging job with error: {0}".format(
                        data_aging_job.delay_reason
                    )
                )
            self.log.info("Data aging job is finished")

            self.log.info("Stopping postgres server and cleaning up data and wal directory...")
            self.postgres_helper_object.cleanup_database_directories()
            self.run_restore(no_of_streams=2)
            self.log.info("Re-establishing connection with postgres server")
            self.pgsql_db_object.reconnect()
            db_info_after_restore = self.get_metadata()
            self.validate_data(db_info_before_restore, db_info_after_restore)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
