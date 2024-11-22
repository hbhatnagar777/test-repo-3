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

    _run_backup()   --  Initiates the backup job for the fs subclient

    validation()    --  method to validate standby backup

    run()           --  Main function for test case execution

Input Example:

    "testCases":
            {
                "59074":
                        {
                            "ClientName": "pgtestunix",
                            "AgentName": "POSTGRESQL",
                            "InstanceName": "pgtestunix_5444",
                            "BackupsetName": "fsbasedbackupset",
                            "SubclientName": "default"
                        }
            }

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper


class TestCase(CVTestCase):
    """Class for executing PostgreSQL standby TC - log shipping"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "PostgreSQL standby TC - log shipping"
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.pgsql_db_object = None
        self.standby_client = None
        self.standby_instance = None
        self.standby_postgres_helper_object = None
        self.standby_data_directory = None
        self.backupset = None
        self.subclient = None

    def setup(self):
        """setup function for this testcase"""
        if not self.instance.is_standby_enabled:
            raise Exception("Standby is not enabled")
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        if self.postgres_helper_object.is_streaming_replication:
            raise Exception(
                "Postgres server is not in log shipping mode")
        standby_instance_name = self.instance.standby_instance_name
        standby_instance_id = self.instance.standby_instance_id
        standby_client_name = self.postgres_helper_object.get_standby_client_name(
            standby_instance_id)
        self.log.info(
            f"Standby client: {standby_client_name} and standby instance: {standby_instance_name}")
        self.standby_client = self.commcell.clients.get(standby_client_name)
        self.standby_instance = self.standby_client.agents.get(
            'postgresql').instances.get(standby_instance_name)
        self.standby_postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.standby_client, self.standby_instance)
        if not self.standby_postgres_helper_object.is_pg_in_recovery:
            raise Exception(
                "Standby node is not in recovery mode, please check the setup")
        self.standby_data_directory = self.standby_postgres_helper_object.get_postgres_data_dir(
            self.standby_instance.postgres_bin_directory,
            self.standby_postgres_helper_object.postgres_password,
            self.standby_instance.postgres_server_port_number)

        self.log.info("Disabling user master for data and log backup")
        self.instance.use_master_for_data_backup = False
        self.instance.use_master_for_log_backup = False

    def _run_backup(self, backup_type):
        """Initiates the backup job for the specified subclient

        Args:

            backup_type          (str)       -- Type of backup (FULL/INCREMENTAL)

        Returns:
            job                              -- Object of Job class

        Raises:
            Exception:
                if unable to start the backup job

        """
        self.log.info(
            f' #### Running {backup_type} Backup ####')
        job = self.subclient.backup(backup_type)
        self.log.info(
            "Started %s backup with Job ID: %s", backup_type, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run %s backup job with error: %s" % (
                    backup_type, job.delay_reason)
            )
        self.log.info("Successfully finished %s backup job", backup_type)

        return job

    def validation(self, job_id, backup_phase="DATA"):
        """ method to validate standby backup

        Args:

            job_id           (str)  --  Backup job ID

            backup_phase    `(str)  --  Phase of backup (DATA/LOG)

        Raises:
            Exception:
                if log backup run on master/slave when the option is not set

                if data backup run on master when the option is not set

        """
        self.log.info(f"Validating for job:{job_id} and Phase:{backup_phase}")
        if self.standby_postgres_helper_object.is_backup_run_on_standby(
                job_id, backup_phase):
            self.log.info(f"{backup_phase} backup phase is run on standby")
            if self.instance.use_master_for_log_backup and 'log' in backup_phase.lower():
                self.log.error(
                    "log backup was expected to run on master - as the setting is provided")
                raise Exception(
                    "log backup was expected to run on master - as the setting is provided")
        else:
            self.log.info(f"{backup_phase} backup phase is run on master")
            if 'data' in backup_phase.lower():
                self.log.info("Standby server must be down so the data backup was run on master")
            if 'log' in backup_phase.lower():
                if self.instance.use_master_for_log_backup:
                    self.log.info("Log backup is run on master as per setting")
                else:
                    self.log.error("Log backup was run on master without enabling option")
                    raise Exception("Log backup was run on master without enabling option")
            if not self.instance.use_master_for_data_backup and 'data' in backup_phase.lower():
                self.log.error(
                    "Data backup phase cannot run on master as use master option is disabled")
                raise Exception(
                    "Data backup phase cannot run on master as use master option is disabled")

    def run(self):
        """Main function for test case execution"""
        try:
            job = self._run_backup("FULL")
            self.validation(job.job_id)
            self.validation(job.job_id, "LOG")
            job = self._run_backup("INCREMENTAL")
            self.validation(job.job_id, "LOG")

            self.instance.use_master_for_log_backup = True
            job = self._run_backup("INCREMENTAL")
            self.validation(job.job_id, "LOG")

            self.log.info("Bring down standby postgres server")
            self.standby_postgres_helper_object.stop_postgres_server(
                self.standby_instance.postgres_bin_directory, self.standby_data_directory)
            self.log.info("Enabled use master if standby not available option")
            self.instance.use_master_for_data_backup = True
            job = self._run_backup("FULL")
            self.validation(job.job_id)
            self.validation(job.job_id, "LOG")
            self.standby_postgres_helper_object.start_postgres_server(
                self.standby_instance.postgres_bin_directory, self.standby_data_directory)
            if self.standby_postgres_helper_object.machine_object.check_file_exists(
                    self.standby_postgres_helper_object.machine_object.join_path(
                        self.standby_data_directory, "backup_label")):
                raise Exception("backup label file still exists in standby data directory.")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
