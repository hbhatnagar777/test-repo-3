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
        self.name = "Restartability Test of PostgreSQL iDA - 2"
        self.product = self.products_list.POSTGRESQL
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True

    def _run_backup(
            self,
            sub_client,
            backup_type,
            suspend=True):
        """Initiates backup job, Suspends the job if the suspend
        flag is set and waits for completion.

            Args:

                sub_client          (object)    --  instance of subclient class

                backup_type         (str)       --  Type of backup to perform(FULL/INCREMENTAL etc)

                suspend             (boolean)   --  Performs suspend operation if the suspend
                flag is set

            Returns:

                job                 (object)    --  returns the instance of Job class for the backup
                it started

        """

        self.log.info(
            "*" *
            10 +
            " Starting Subclient {0} Backup ".format(backup_type) +
            "*" *
            10)

        db_helper_object = dbhelper.DbHelper(self.commcell)
        job = sub_client.backup(backup_type)
        self.log.info(
            "Started %s backup with Job ID: %s",
            backup_type,
            job.job_id)
        # Perform suspend operations if suspend option is selected
        if suspend:
            interrupt_object = interruption.Interruption(
                job.job_id, self.commcell)
            self.log.info(
                "Sleeping for 10 seconds before performing suspend operation")
            time.sleep(10)

            # suspend and resume the job
            interrupt_object.suspend_resume_job()

            ############################## Check for the chunk commit##########
            self.log.info("checking for the chunk commit")
            response = False
            while (not response) and ("completed" not in job.status.lower()):
                response = db_helper_object.check_chunk_commited(
                    job.job_id)
                if not response:
                    time.sleep(120)
            self.log.info(
                "Proceeding to kill a random process as atleast one chunk is commited")

            #### Kill a random process ####
            self.log.info(
                "Sleeping 30 seconds before introducing next interrupt")
            time.sleep(30)
            interrupt_object.random_process_kill()

            # reboot the client to suspend the job
            self.log.info(
                "Sleeping 30 seconds before introducing next interrupt")
            time.sleep(30)
            interrupt_object.reboot_client()

        ######################### Wait for the job completion #################

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )

        self.log.info("Successfully finished %s backup job", backup_type)
        return job

    def _run_restore(
            self,
            sub_client,
            database_list,
            client_name,
            instance_name):
        """Initiates restore job and waits for completion.

            Args:

                sub_client      (object)     --  instance of subclient class

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
        backupset_name = sub_client._backupset_object.backupset_name
        self.log.info(
            "*" *
            10 +
            " Starting Subclient associated with backupset {0} Restore ".format(backupset_name) +
            "*" *
            10)
        job = sub_client.restore_postgres_server(
            database_list, client_name, instance_name)
        self.log.info(
            "Started %s Restore with Job ID: %s", backupset_name, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: {0}".format(
                    job.delay_reason
                )
            )

        self.log.info(
            "Successfully finished %s restore job", backupset_name)

        return job

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)

            postgres_helper_object = pgsqlhelper.PostgresHelper(
                self.commcell, self.client, self.instance)
            machine_object = machine.Machine(
                self.client, self.commcell)

            # Specifying Maintanance Database and Template0 -- hard coded right
            # now
            ignore_db_list = ["postgres", "template0", "template1"]
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

            backup_set = self.instance.backupsets.get("dumpbasedbackupset")
            default_subclient_name = backup_set.subclients.default_subclient
            self.log.info("Default Subclient is:%s", default_subclient_name)
            sub_client = backup_set.subclients.get(default_subclient_name)
            self.log.info("Getting subclient list")
            sub_client_list = list(backup_set.subclients.all_subclients.keys())
            self.log.info("Subclient List: %s", sub_client_list)

            db_list_before_backup = None
            # Get Subclient content
            # check if subclient exists or not. If not default subclient
            self.log.info("Collecting DB List")
            if sub_client.subclient_name.lower() == backup_set.subclients.default_subclient.lower():
                db_list_before_backup = pgsql_db_object.get_db_list()
                if db_list_before_backup is None:
                    raise Exception(
                        "Unable to get the database list"
                    )
                # Get list of all the subclients content and exclude them from total list
                # of Databases
                all_other_sub_clients_contents = list()
                for sbclnt in sub_client_list:
                    if sbclnt.lower() != backup_set.subclients.default_subclient.lower():
                        self.log.info(
                            "Subclient name is not default subclient")
                        subclient_new = backup_set.subclients.get(sbclnt)
                        subc_content_db_list = subclient_new.content
                        all_other_sub_clients_contents = (
                            all_other_sub_clients_contents + subc_content_db_list)
                for db_name in all_other_sub_clients_contents:
                    if db_name in db_list_before_backup:
                        db_list_before_backup.remove(db_name)

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

            # Collecting size of app after first backup without suspend
            job = self._run_backup(
                sub_client,
                "FULL",
                suspend=False)
            size_of_app_after_first_backup = int(
                postgres_helper_object.get_size_of_app_in_backup_phase(
                    job.job_id))
            self.log.info(
                "size of app after first backup is=%sMB",
                size_of_app_after_first_backup)
            size_of_app_after_first_backup = size_of_app_after_first_backup
            size_of_app_after_first_backup = round(
                size_of_app_after_first_backup, 2)
            self.log.info(
                "size of app after first backup is=%sGB",
                size_of_app_after_first_backup)
            time.sleep(15)

            ##################### Running Full Backup ########################
            job = self._run_backup(sub_client, "FULL")
            self.log.info(
                "Collecting the size of application details after the backup")
            size_of_app_after_second_backup = int(
                postgres_helper_object.get_size_of_app_in_backup_phase(
                    job.job_id))
            self.log.info(
                "size of app after second backup is=%sMB",
                size_of_app_after_second_backup)
            size_of_app_after_second_backup = size_of_app_after_second_backup
            size_of_app_after_second_backup = round(
                size_of_app_after_second_backup, 2)
            self.log.info(
                "size of app after second backup is=%sGB",
                size_of_app_after_second_backup)

            ######size of application validation############
            if int((((size_of_app_after_second_backup - size_of_app_after_first_backup) /
                     size_of_app_after_first_backup) * 100)) <= 20:
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
            postgres_helper_object.cleanup_test_data(db_list, pgsql_db_object)

            ####################### Running restore ###########################
            self._run_restore(
                sub_client,
                db_list,
                self.client.client_name,
                self.instance.instance_name)
            db_list_after_restore = pgsql_db_object.get_db_list()
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
            if not return_code:
                raise Exception(
                    "Database information validation failed."
                )
            self.log.info(
                "Database information validation passed successfully")

            ########################## FS Backup/Restore Operation ##########

            # Running FS Backup FULL
            backup_set = self.instance.backupsets.get("fsbasedbackupset")
            default_subclient_name = backup_set.subclients.default_subclient
            sub_client = backup_set.subclients.get(default_subclient_name)

            # collecting data_dir and pg_xlog directory size to compare with size of
            # application in backup phase
            version = self.instance.postgres_version
            version = int(version.split(".")[0])
            log_dir_name = "pg_xlog"
            if version > 9:
                log_dir_name = "pg_wal"

            command_1 = "du -smL {0}".format(postgres_data_directory)
            command_2 = "du -sm {0}/{1}".format(postgres_data_directory, log_dir_name)
            command_3 = "du -sm {0}".format(postgres_archive_log_directory)
            if "windows" in machine_object.os_info.lower():
                command_1 = ("(Get-ChildItem \"{0}\" -Recurse | Measure-Object "
                             "-Property Length -Sum -ErrorAction Stop).Sum / 1MB".format(
                                 postgres_data_directory))
                command_2 = ("(Get-ChildItem \"{0}/{1}\" -Recurse | Measure-Object"
                             " -Property Length -Sum -ErrorAction Stop).Sum / 1MB".format(
                                 postgres_data_directory, log_dir_name))
                command_3 = ("(Get-ChildItem \"{0}\" -Recurse | Measure-Object "
                             "-Property Length -Sum -ErrorAction Stop).Sum / 1MB".format(
                                 postgres_archive_log_directory))

            size_of_data_dir = machine_object.execute_command(
                command_1).formatted_output
            size_of_pg_xlog = machine_object.execute_command(
                command_2).formatted_output
            size_of_wal_dir = machine_object.execute_command(
                command_3).formatted_output

            if "unix" in machine_object.os_info.lower():
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
            ###################### Running Full Backup ########################
            job = self._run_backup(sub_client, "FULL")

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
                     size_of_app_before_backup) * 100)) <= 20:
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

            # Running FS Backup Log
            self._run_backup(sub_client, "INCREMENTAL")

            self.log.info("Sleeping for 240 seconds")
            time.sleep(240)

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
                sub_client,
                ["/data"],
                self.client.client_name,
                self.instance.instance_name)
            postgres_helper_object.refresh()

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
            if not return_code:
                raise Exception(
                    "Database information validation failed."
                )
            self.log.info(
                "Database information validation passed successfully")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
