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

    validate_data()     --  validates the data in source and destination

    sync_operation()    --  method to performs live sync operation and validations

    tear_down()         --  tear down function to delete automation
    generated data

    run()               --  Main function for test case execution

"""
from cvpysdk import schedules
from AutomationUtils import constants, database_helper
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.dbhelper import DbHelper

class TestCase(CVTestCase):
    """Class for executing LIVE SYNC testcase for PostgreSQL iDA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Live Sync for PostgreSQL iDA"
        self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.POSTGRESQL
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            'DestinationClient': None,
            'DestinationInstance': None
        }
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.pgsql_db_object = None
        self.schedule_object = None
        self.destination_client = None
        self.destination_agent = None
        self.destination_instance = None
        self.destination_pg_helper_object = None
        self.destination_postgres_password = None

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
        self.schedule_object = schedules.Schedules(self.backupset)
        self.destination_client = self.commcell.clients.get(self.tcinputs['DestinationClient'])
        self.destination_agent = self.destination_client.agents.get('postgresql')
        self.destination_instance = self.destination_agent.instances.get(
            self.tcinputs['DestinationInstance'])
        self.destination_pg_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.destination_client, self.destination_instance)
        self.destination_postgres_password = self.destination_pg_helper_object.postgres_password

    def get_metadata(
            self,
            postgres_db_object,
            postgres_helper_object,
            client,
            instance,
            postgres_password):
        """ method to collect database information

            Args:
                postgres_db_object       (obj)  --  postgres database object

                postgres_helper_object   (obj)  --  postgres helper object

                client                   (obj)  --  client object

                instances                (obj)  --  Instance object

                postgres_password        (str)  --  postgres server password

            Returns:
                dict        --      meta data info of database

            Raises:
                Exception:
                    if unable to get the database list

        """
        # Colecting Meta data after inc backup
        database_list = postgres_db_object.get_db_list()
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
        return postgres_helper_object.generate_db_info(
            database_list,
            client.client_hostname,
            instance.postgres_server_port_number,
            instance.postgres_server_user_name,
            postgres_password)

    def validate_data(self, db_info_source, db_info_destination):
        """validates the data in source and destination

            Args:
                db_info_source        (dict)  --  database information of source

                db_info_destination   (dict)  --  database information of destination

            Raises:
                Exception:

                    if database information validation failed

        """

        self.log.info("Validating the database information collected before SNAP \
            Incremental 2nd Backup and after clone Restore")
        if not self.postgres_helper_object.validate_db_info(
                db_info_source, db_info_destination):
            raise Exception(
                "Database information validation failed."
            )
        else:
            self.log.info(
                "Database information validation passed successfully")

    def sync_operation(self, job):
        """method to performs live sync operation and validations

            Args:
                job         (obj)   --      backup job object

            Raises:
                Exception

                    if failed to run replication job

                    if destination server is not in recovery mode

        """
        replication_job = self.postgres_helper_object.get_replication_job(job)
        if not replication_job.wait_for_completion():
            raise Exception(
                "Failed to run replication job with error: {0}".format(
                    replication_job.delay_reason
                )
            )
        self.log.info("replication job: %s is completed", replication_job.job_id)

        if not self.destination_pg_helper_object.check_postgres_recovery_mode():
            self.log.info("Destination server is not in recovery mode.!")
            raise Exception("Destination server is not in recovery mode.!")

        self.log.info(
            "Destination server is in recovery mode, continuing ahead with test case execution")

        db_info_before_backup = self.get_metadata(
            self.pgsql_db_object,
            self.postgres_helper_object,
            self.client,
            self.instance,
            self.postgres_db_password)

        destination_pgsql_db_object = database_helper.PostgreSQL(
            self.destination_client.client_hostname,
            self.destination_instance.postgres_server_port_number,
            self.destination_instance.postgres_server_user_name,
            self.destination_postgres_password,
            "postgres")

        db_info_after_restore = self.get_metadata(
            destination_pgsql_db_object,
            self.destination_pg_helper_object,
            self.destination_client,
            self.destination_instance,
            self.destination_postgres_password)
        self.validate_data(db_info_before_backup, db_info_after_restore)


    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "auto")
        self.log.info("Deleting schedule")
        self.schedule_object.refresh()
        self.schedule_object.delete("automation")


    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)

            self.log.info("Checking if schedule is already present, deleting schedule if present.")
            self.schedule_object = schedules.Schedules(self.backupset)
            if self.schedule_object.has_schedule("automation"):
                self.schedule_object.delete("automation")

            dbhelper_object = DbHelper(self.commcell)

            ############ Live Sync Operation ##########
            self.log.info("##### Live Sync Operations #####")
            self.log.info("Adding data before running FULL backup")
            self.log.info("Generating Test Data")
            self.postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                3,
                5,
                250,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_db_password,
                True,
                "auto")

            ### run full backup
            self.log.info("###Starting FULL backup job###")
            full_job = dbhelper_object.run_backup(self.subclient, "FULL")

            self.log.info("Performing live sync configuration")
            self.backupset.run_live_sync(
                self.tcinputs['DestinationClient'],
                self.tcinputs['DestinationInstance'],
                full_job)


            self.log.info("Stopping destination server if not already stopped.!")


            postgres_data_directory = self.destination_pg_helper_object.get_postgres_data_dir(
                self.destination_instance.postgres_bin_directory,
                self.destination_postgres_password,
                self.destination_instance.postgres_server_port_number)
            self.log.info("Stopping destination server")
            self.destination_pg_helper_object.stop_postgres_server(
                self.destination_instance.postgres_bin_directory,
                postgres_data_directory)
            self.log.info("Stopped destination postgres server")

            self.log.info("Live Sync Configuration is success")
            self.log.info("Getting the replication Job")

            self.sync_operation(full_job)

            self.log.info("Adding more data before incremental")
            self.postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                1,
                5,
                100,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_db_password,
                True,
                "auto_inc")
            self.log.info("###Starting Incremental backup job###")
            inc_job = dbhelper_object.run_backup(self.subclient, "Incremental")
            self.sync_operation(inc_job)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
