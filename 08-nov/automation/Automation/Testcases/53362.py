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

    __init__()          --  initialize TestCase class

    _run_backup()       --  initiates the backup job for the specified subclient

    _run_restore()      --  initiates the restore job for the specified subclient

    run()               --  run function of this test case

"""
import re
import time
from AutomationUtils import database_helper, machine, constants, interruption
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database import dbhelper


class TestCase(CVTestCase):
    """Class for executing Restartability test of PostgreSQL iDA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Suspending Jobs in different Phases PostgreSQL iDA"
        self.product = self.products_list.POSTGRESQL
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            'MALargeFileLocation': None
        }
        self.index_version = None
        self.subclient = None
        self.backupset = None

    def _run_backup(
            self,
            backup_type,
            suspend=True):
        """Initiates backup job, Suspends the job if the suspend
        flag is set and waits for completion.

            Args:

                backup_type         (str)       --  Type of backup to perform(FULL/INCREMENTAL etc)

                suspend             (boolean)   --  Performs suspend operation if the suspend
                flag is set

            Returns:

                job                 (object)    --  returns the instance of Job class for the backup
                it started

        """

        self.log.info("***** Starting Subclient %s Backup *****", backup_type)

        db_helper_object = dbhelper.DbHelper(self.commcell)
        job = self.subclient.backup(backup_type)
        self.log.info(
            "Started %s backup with Job ID: %s",
            backup_type,
            job.job_id)
        # Perform suspend operations if suspend option is selected
        ma_machine_object = None
        indexing_directory_path = None
        if suspend:
            interrupt_object = interruption.Interruption(
                job.job_id, self.commcell)
            if "scan" in job.phase.lower():
                self.log.info("Suspending Job in Scan Phase")
                interrupt_object.restart_client_services()

            ################ Checking if the large file exists ###########
            ma_client_object = self.commcell.clients.get(interrupt_object._media_agent_name)
            ma_machine_object = machine.Machine(ma_client_object, self.commcell)
            self.log.info("Checking if the large file exists.")
            if not ma_machine_object.check_file_exists(self.tcinputs["MALargeFileLocation"]):
                raise Exception("Large file is not found in the specified location of MA.")
            self.log.info("Large file exists in specified location")

            while "backup" not in job.phase.lower():
                if job.is_finished:
                    self.log.info("Job is already finished")
                    return job
                time.sleep(10)
            ######### copy large file to the index directory path
            index_version = 1
            if self.index_version:
                index_version = 2
            indexing_directory_path = db_helper_object.get_index_cache_path(
                job.job_id,
                ma_machine_object,
                self.backupset,
                index_version)
            self.log.info("Copying Large file to index cache location")
            ma_machine_object.copy_folder(
                self.tcinputs["MALargeFileLocation"],
                indexing_directory_path)
            self.log.info("Large file is copied to index cache location")
            self.log.info("Now the archive index phase will run for longer time")
            self.log.info("Waiting for backup phase to begin to interrupt the job")
            self.log.info("Waiting for 5 seconds before suspending the job")
            time.sleep(5)
            self.log.info("Suspending Job in Backup Phase")
            interrupt_object.restart_client_services()
            self.log.info("Waiting for archive index phase to begin to interrupt the job")
            while "archive index" not in job.phase.lower():
                if job.is_finished:
                    self.log.info("Job is already finished")
                    return job
                time.sleep(10)
            self.log.info("Suspending Job in Archive Index Phase")
            self.log.info("Waiting for 5 seconds before suspending the job")
            time.sleep(5)
            interrupt_object.suspend_resume_job()

        ######################### Wait for the job completion #################

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )

        self.log.info("Successfully finished %s backup job", backup_type)
        if suspend:
            indexing_directory_path = indexing_directory_path.split(
                str(self.subclient.subclient_id))[0]
            indexing_directory_path = ma_machine_object.join_path(
                indexing_directory_path,
                str(self.subclient.subclient_id))
            self.log.info(
                "Removing contents of Archive index directory for this Job from: %s",
                indexing_directory_path)
            ma_machine_object.remove_directory(indexing_directory_path)
            self.log.info("Removed contents of Archive index directory for this Job")
        return job

    def _run_restore(
            self,
            database_list,
            client_name,
            instance_name):
        """Initiates restore job and waits for completion.

            Args:

                database_list   (list)       --  list of database to restore

                client_name     (str)        --  Name of the client

                instance_name   (str)        --  Name of the instance

            Returns:

                job            (object)    --  returns the instance of Job class
                                               for the restore it started

        """
        self.log.debug("Database list to restore = %s", database_list)
        self.log.debug("client Name = %s", client_name)
        self.log.debug("instanceName = %s", instance_name)
        self.log.info("***** Starting Subclient associated with backupset Restore *****")
        job = self.subclient.restore_postgres_server(
            database_list, client_name, instance_name)
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

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)

            postgres_helper_object = pgsqlhelper.PostgresHelper(
                self.commcell, self.client, self.instance)
            self.index_version = postgres_helper_object.is_index_v2_postgres

            # Specifying Maintanance Database and Template0 -- hard coded right
            # now
            ignore_db_list = ["postgres", "template0"]
            postgres_server_user_password = postgres_helper_object._postgres_db_password

            self.log.info(
                "Postgres BIN Directory Path:%s",
                self.instance.postgres_bin_directory)
            postgres_data_directory = postgres_helper_object.get_postgres_data_dir(
                self.instance.postgres_bin_directory,
                postgres_server_user_password,
                self.instance.postgres_server_port_number)
            postgres_archive_log_directory = self.instance.postgres_archive_log_directory
            self.log.info(
                "Postgres Data Directory Path:%s",
                postgres_data_directory)
            self.log.info(
                "Postgres arch LOG Directory Path:%s",
                postgres_archive_log_directory)
            pgsql_db_object = database_helper.PostgreSQL(
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                postgres_server_user_password,
                "postgres")

            ############### DumpBased Backup/Restore Operations #############

            self.backupset = self.instance.backupsets.get("dumpbasedbackupset")
            default_subclient_name = self.backupset.subclients.default_subclient
            self.log.info("Default Subclient is:%s", default_subclient_name)
            self.subclient = self.backupset.subclients.get(default_subclient_name)
            self.log.info("Getting subclient list")

            db_list_before_backup = postgres_helper_object.get_subclient_database_list(
                self.subclient.subclient_name,
                self.backupset,
                pgsql_db_object.get_db_list())

            # Get the subclient content Info before backup
            self.log.info(
                "Collect information of the subclient content before backup")
            for i in ignore_db_list:
                if i in db_list_before_backup:
                    db_list_before_backup.remove(i)

            self.log.info("DB list before backup: %s", db_list_before_backup)

            # Colecting Meta data
            db_info_before_full_backup = postgres_helper_object.generate_db_info(
                db_list_before_backup,
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                postgres_server_user_password)
            self.log.info(
                "MetaData details before backup: %s",
                db_info_before_full_backup)

            #########Collecting size of app after first backup without suspend
            job = self._run_backup(
                "FULL",
                suspend=False)
            size_of_app_after_first_backup = int(
                postgres_helper_object.get_size_of_app_in_backup_phase(
                    job.job_id))
            self.log.info(
                "size of app after first backup is=%sMB",
                size_of_app_after_first_backup)
            size_of_app_after_first_backup = size_of_app_after_first_backup / 1024
            size_of_app_after_first_backup = round(
                size_of_app_after_first_backup, 2)
            self.log.info(
                "size of app after first backup is=%sGB",
                size_of_app_after_first_backup)
            time.sleep(15)

            ##################### Running Full Backup ########################
            job = self._run_backup("FULL")
            self.log.info(
                "Collecting the size of application details after the backup")
            size_of_app_after_second_backup = int(
                postgres_helper_object.get_size_of_app_in_backup_phase(
                    job.job_id))
            self.log.info(
                "size of app after second backup is=%sMB",
                size_of_app_after_second_backup)
            size_of_app_after_second_backup = size_of_app_after_second_backup / 1024
            size_of_app_after_second_backup = round(
                size_of_app_after_second_backup, 2)
            self.log.info(
                "size of app after second backup is=%sGB",
                size_of_app_after_second_backup)

            ######size of application validation############
            if int((((size_of_app_after_second_backup - size_of_app_after_first_backup) /
                     size_of_app_after_first_backup) * 100)) <= 10:
                self.log.info("Size of application validation is success..!!")
            else:
                raise Exception(
                    "Unable to validate using size of application."
                )

            # appending "/" to dbnames for dumpbased restore
            db_list = ["/" + ele for ele in db_list_before_backup]

            self.log.info("Sleeping for 10 seconds")
            time.sleep(10)

            self.log.info("Deleting Automation Created databases")
            postgres_helper_object.cleanup_tc_db(
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                postgres_server_user_password,
                "auto")

            ####################### Running restore ###########################
            self._run_restore(
                db_list,
                self.client.client_name,
                self.instance.instance_name)
            db_list_after_restore = postgres_helper_object.get_subclient_database_list(
                self.subclient.subclient_name,
                self.backupset,
                pgsql_db_object.get_db_list())
            self.log.info("DB list after restore:%s", db_list_after_restore)
            if db_list_after_restore is None:
                raise Exception(
                    "Unable to get the database list."
                )

            # Get subclient content info after restore
            self.log.info(
                "Collect information of the subclient content after restore")
            for i in ignore_db_list:
                if i in db_list_after_restore:
                    db_list_after_restore.remove(i)
            db_info_after_restore = postgres_helper_object.generate_db_info(
                db_list_after_restore,
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                postgres_server_user_password)

            # validation
            self.log.info(
                "Validating the database information collected before \
                Full Backup and after Inplace Restore for DumpBasedBackupset")
            # validate subclient content information collected before backup
            # and after restore
            return_code = postgres_helper_object.validate_db_info(
                db_info_before_full_backup, db_info_after_restore)
            if return_code != True:
                raise Exception(
                    "Database information validation failed."
                )
            else:
                self.log.info(
                    "Database information validation passed successfully")

            ########################## FS Backup/Restore Operation ##########

            # Running FS Backup FULL
            self.backupset = self.instance.backupsets.get("fsbasedbackupset")
            default_subclient_name = self.backupset.subclients.default_subclient
            self.subclient = self.backupset.subclients.get(default_subclient_name)

            # collecting data_dir and pg_xlog directory size to compare with size of
            # application in backup phase

            command_1 = "du -smL {0}".format(postgres_data_directory)
            command_2 = "du -sm {0}/pg_xlog".format(postgres_data_directory)
            command_3 = "du -sm {0}".format(postgres_archive_log_directory)
            if "windows" in postgres_helper_object.machine_object.os_info.lower():
                command_1 = ("(Get-ChildItem \"{0}\" -Recurse | Measure-Object "
                             "-Property Length -Sum -ErrorAction Stop).Sum / 1MB".format(
                                 postgres_data_directory))
                command_2 = ("(Get-ChildItem \"{0}/pg_xlog\" -Recurse | Measure-Object"
                             " -Property Length -Sum -ErrorAction Stop).Sum / 1MB".format(
                                 postgres_data_directory))
                command_3 = ("(Get-ChildItem \"{0}\" -Recurse | Measure-Object "
                             "-Property Length -Sum -ErrorAction Stop).Sum / 1MB".format(
                                 postgres_archive_log_directory))

            size_of_data_dir = postgres_helper_object.machine_object.execute_command(
                command_1).formatted_output
            size_of_pg_xlog = postgres_helper_object.machine_object.execute_command(
                command_2).formatted_output
            size_of_wal_dir = postgres_helper_object.machine_object.execute_command(
                command_3).formatted_output

            if "unix" in postgres_helper_object.machine_object.os_info.lower():
                size_of_data_dir = int(re.split(r'\t+', size_of_data_dir)[0])
                size_of_pg_xlog = int(re.split(r'\t+', size_of_pg_xlog)[0])
                size_of_wal_dir = int(re.split(r'\t+', size_of_wal_dir)[0])
            else:
                size_of_data_dir = int(size_of_data_dir.split('.')[0])
                size_of_pg_xlog = int(size_of_pg_xlog.split('.')[0])
                size_of_wal_dir = int(size_of_wal_dir.split('.')[0])

            size_of_app_before_backup = (
                size_of_data_dir - size_of_pg_xlog) / 1024
            size_of_app_before_backup = round(size_of_app_before_backup, 1)
            size_of_wal_before_backup = round((size_of_wal_dir / 1024), 1)

            self.log.info(
                "size_of_app_before_backup is=%sGB",
                size_of_app_before_backup)
            self.log.info(
                "size_of_wal_dir_before_backup is=%sGB",
                size_of_wal_before_backup)
            time.sleep(15)
            ##################### Running Full Backup ########################
            job = self._run_backup("FULL")

            size_of_app_after_backup = int(
                postgres_helper_object.get_size_of_app_in_backup_phase(
                    job.job_id))
            size_of_app_after_backup = size_of_app_after_backup / 1024
            size_of_app_after_backup = round(size_of_app_after_backup, 1)
            self.log.info(
                "size_of_app_after_backup is=%sGB",
                size_of_app_after_backup)
            size_of_app_log_phase_after_backup = int(
                postgres_helper_object.get_size_of_app_in_backup_phase(
                    job.job_id, 11))
            self.log.info("size_of_app_in log_phase_after_backup is=%sMB", (
                size_of_app_log_phase_after_backup))
            size_of_app_log_phase_after_backup = size_of_app_log_phase_after_backup / 1024
            size_of_app_log_phase_after_backup = round(
                size_of_app_log_phase_after_backup, 1)
            self.log.info("size_of_app_in log_phase_after_backup is=%sGB", (
                size_of_app_log_phase_after_backup))

            ######size of application validation############
            if int((((size_of_app_after_backup - size_of_app_before_backup) /
                     size_of_app_before_backup) * 100)) <= 10:
                self.log.info("Size of application validation is success..!!")
            else:
                raise Exception(
                    "Unable to validate Backup data using size of application."
                )

            # Colecting Meta data
            db_list_before_backup = pgsql_db_object.get_db_list()
            if db_list_before_backup is None:
                raise Exception(
                    "Unable to get the database list."
                )
            # Get the subclient content Info before backup
            self.log.info(
                "Collect information of the subclient content before backup")
            for i in ignore_db_list:
                if i in db_list_before_backup:
                    db_list_before_backup.remove(i)

            db_info_before_full_backup = postgres_helper_object.generate_db_info(
                db_list_before_backup,
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                postgres_server_user_password)

            time.sleep(10)
            self.log.info("Sleeping for 10 seconds")

            # stopping postgres server before the restore
            return_code = postgres_helper_object.stop_postgres_server(
                self.instance.postgres_bin_directory,
                postgres_data_directory)
            if return_code:
                self.log.info("Server Stop Success, moving to restore phase")
            else:
                self.log.info(
                    "Server was not running, Continuing to restore phase")

            # Running FS Restore
            self._run_restore(
                ["/data"],
                self.client.client_name,
                self.instance.instance_name)

            del pgsql_db_object
            pgsql_db_object = database_helper.PostgreSQL(
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                postgres_server_user_password,
                "postgres")

            # Colecting Meta data
            db_list_after_restore = pgsql_db_object.get_db_list()
            if db_list_after_restore is None:
                raise Exception(
                    "Unable to get the database list."
                )
            self.log.info(
                "Collect information of the subclient content after restore")
            for i in ignore_db_list:
                if i in db_list_after_restore:
                    db_list_after_restore.remove(i)

            db_info_after_restore = postgres_helper_object.generate_db_info(
                db_list_after_restore,
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                postgres_server_user_password)

            # validation using meta data

            self.log.info("Validating the database information collected before Full \
                Backup and after Inplace Restore for FSBased Backup")
            # validate subclient content information collected before backup
            # and after restore
            return_code = postgres_helper_object.validate_db_info(
                db_info_before_full_backup, db_info_after_restore)
            if return_code != True:
                raise Exception(
                    "Database information validation failed."
                )
            else:
                self.log.info(
                    "Database information validation passed successfully")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
