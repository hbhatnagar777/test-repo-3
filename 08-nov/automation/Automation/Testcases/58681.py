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
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper


class TestCase(CVTestCase):
    """Class for executing PostgreSQL TC"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Backup should complete with error if DBs are missing from user subclient"
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

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "auto_user_db")
        if self.backupset.subclients.has_subclient('test'):
            self.backupset.subclients.delete('test')

    def run(self):
        """Main function for test case execution"""

        try:
            if self.backupset.subclients.has_subclient('test'):
                self.backupset.subclients.delete('test')
            self.log.info("Generating Test Data")
            self.postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                3,
                10,
                100,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_db_password,
                True,
                "auto_user_db")
            self.log.info("Test Data Generated successfully")

            self.log.info("Creating user subclient")
            storage_policy = self.backupset.subclients.get("default").storage_policy
            subclient_object = self.backupset.subclients.add_postgresql_subclient(
                "test", storage_policy, ['auto_user_db_testdb_0', 'auto_user_db_testdb_1'])

            self.log.info("Delete one of the databases in the content")
            self.pgsql_db_object.drop_db('auto_user_db_testdb_0')


            ###################### Running Full Backup ##############################
            self.log.info(
                "#" * (10) + "  Running Dumpbased Full Backup  " + "#" * (10))
            job_object = self._run_backup(subclient_object, "FULL")

            if not "completed w/ one or more errors" in job_object.status.lower():
                raise Exception("Job completed even when a database is missing.")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
