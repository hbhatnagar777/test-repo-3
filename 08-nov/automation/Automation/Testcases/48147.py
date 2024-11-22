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

    _run_restore()  --  Initiates the restore job for the specified subclient

    run()           --  Main function for test case execution

"""
import ast
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.dbhelper import DbHelper

class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of PostgreSQL SNAP backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "ACCT1- PostgreSQL Snap Feature"
        self.show_to_user = True
        self.tcinputs = {
            'TestDataSize': None
        }
        self.postgres_data_population_size = None
        self.postgres_helper_object = None
        self.postgres_server_user_password = None
        self.pgsql_db_object = None

    def setup(self):
        """ setup method for this testcase """
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.postgres_server_user_password = self.postgres_helper_object.postgres_password
        self.pgsql_db_object = self.postgres_helper_object._get_postgres_database_connection(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_server_user_password,
            "postgres")
        if isinstance(self.tcinputs['TestDataSize'], str):
            self.tcinputs['TestDataSize'] = ast.literal_eval(self.tcinputs['TestDataSize'])

    def restore_validate(self, db_info_before_full_backup, copy_precedence=None):
        """ runs restore and validates data """
        self.postgres_helper_object.cleanup_database_directories()
        # Running FS Restore
        job = self.postgres_helper_object.run_restore(
            ["/data"],
            self.subclient,
            copy_precedence)
        self.postgres_helper_object.refresh()
        self.pgsql_db_object = self.postgres_helper_object._get_postgres_database_connection(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_server_user_password,
            "postgres")

        db_info_after_restore = self.postgres_helper_object.get_metadata()

        self.log.info("Validating the database information collected before SNAP \
            Backup and after Inplace Restore")
        self.postgres_helper_object.validate_db_info(
            db_info_before_full_backup, db_info_after_restore)
        return job

    def tear_down(self):
        """Tear down function"""
        self.log.info("Deleting Automation Created databases")
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_server_user_password,
            "auto")

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", str(self.id))
            self.log.info("Checking if the intelliSnap is enabled on subclient or not")
            if not self.subclient.is_intelli_snap_enabled:
                raise Exception("Intellisnap is not enabled for subclient")
            self.log.info("IntelliSnap is enabled on subclient")

            dbhelper_object = DbHelper(self.commcell)
            self.postgres_data_population_size = self.tcinputs['TestDataSize']

            snap_engine = self.subclient.snapshot_engine_name.lower()
            self.log.info("Snap Engine being used is:%s", snap_engine)

            ########################## SNAP Backup/Restore Operation ##########
            self.log.info("##### SNAP Backup/Restore Operations #####")

            self.log.info("Generating Test Data")
            self.postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                self.postgres_data_population_size[0],
                self.postgres_data_population_size[1],
                self.postgres_data_population_size[2],
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_server_user_password,
                True,
                "auto_snap")
            self.log.info("Test Data Generated successfully")

            ###################### Running Full Backup ########################
            full_job = dbhelper_object.run_backup(self.subclient, "FULL")

            ###### Wait for log backup to complete
            job = dbhelper_object.get_snap_log_backup_job(full_job.job_id)
            self.log.info("Log backup job with ID:%s is now completed", job.job_id)

            db_info_before_full_backup = self.postgres_helper_object.get_metadata()

            if "native" not in snap_engine:
                self.log.info("Snap engine is not native.")
                self.log.info("Sleeping for 20 seconds before starting restore")
                time.sleep(20)

                job = self.restore_validate(db_info_before_full_backup)

                self.log.info("Validating if the data is restored from snap copy or not")
                if not dbhelper_object.check_if_restore_from_snap_copy(job):
                    raise Exception(
                        "Data is not restored from snap copy."
                    )
                self.log.info("validation passed..!! Data is restored form snap copy.")
                ###### Run backup copy job #########
                self.log.info(
                    "Running backup copy job for storage policy: %s",
                    self.subclient.storage_policy)
                copy_precedence = dbhelper_object.run_backup_copy(self.subclient.storage_policy)
                self.log.info("Copy precedence of 'primary snap' copy is: %s", copy_precedence)

            else:
                self.log.info(
                    (
                        "Native Snap engine is being run. backup "
                        "copy job will run inline to snap backup"))
                self.log.info("Getting the backup job ID of backup copy job")
                job = dbhelper_object.get_backup_copy_job(full_job.job_id)
                self.log.info("Job ID of backup copy Job is: %s", job.job_id)

            ############ restore from primary copy ############

            self.log.info("Sleeping for 20 seconds before starting restore")
            time.sleep(20)
            storage_policy_object = self.commcell.storage_policies.get(
                self.subclient.storage_policy)
            copy_precedence = storage_policy_object.get_copy_precedence("primary")

            self.restore_validate(db_info_before_full_backup, copy_precedence)


        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
