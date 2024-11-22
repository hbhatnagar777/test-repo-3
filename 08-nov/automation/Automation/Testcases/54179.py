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

    get_metadata()  --  method to collect database information

    validate_data() --  validates the data in source and destination

    run()           --  Main function for test case execution

"""
import time
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils import machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database import dbhelper


class TestCase(CVTestCase):
    """Class for executing restore to disk feature of PostgreSQL"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Restore to disk feature for PostgreSQL iDA"
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.pgsql_db_object = None
        self.machine_object = None

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
        self.machine_object = machine.Machine(self.client)

    def get_metadata(self):
        """ method to collect database information

            Returns:
                dict        --      meta data info of database

            Raises:
                Exception:
                    if unable to get the database list

        """
        # Collecting Meta data after inc backup
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

        self.log.info(
            "Validating the database information collected before "
            "Incremental Backup and after volume level Restore")
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

            pgsql_server_user_name = self.instance._properties[
                'postGreSQLInstance']['SAUser']['userName']
            pgsql_server_port = self.instance._properties['postGreSQLInstance']['port']
            pgsql_server_hostname = self.client.client_hostname

            pgsql_bin_dir = self.instance._properties['postGreSQLInstance']['BinaryDirectory']
            self.log.info("Bin Directory: %s", pgsql_bin_dir)
            self.log.info("Postgres server Port: %s", pgsql_server_port)

            pgsql_data_dir = self.postgres_helper_object.get_postgres_data_dir(
                pgsql_bin_dir, self.postgres_db_password, pgsql_server_port)
            if "windows" in self.machine_object.os_info.lower():
                pgsql_data_dir = pgsql_data_dir.replace("/", "\\")
            self.log.info("Postgres data directory: %s", pgsql_data_dir)

            pgsql_wal_directory = self.instance.postgres_archive_log_directory

            separator = self.machine_object.os_sep
            restore_to_disk_path = pgsql_data_dir.rsplit(separator, 1)[0]
            restore_to_disk_path = self.machine_object.join_path(
                restore_to_disk_path,
                "restore_to_disk")
            if self.machine_object.check_directory_exists(restore_to_disk_path):
                self.machine_object.remove_directory(restore_to_disk_path)
            self.machine_object.create_directory(restore_to_disk_path)
            if "unix" in self.machine_object.os_info.lower():
                self.machine_object.change_folder_owner("postgres", restore_to_disk_path)
            ############### FS Backup/Restore Operation #################
            self.log.info("Generating Test Data")
            self.postgres_helper_object.generate_test_data(
                pgsql_server_hostname,
                3,
                10,
                100,
                pgsql_server_port,
                pgsql_server_user_name,
                self.postgres_db_password,
                True,
                "auto")
            self.log.info("Test Data Generated successfully")

            # Running FS Backup FULL
            self.log.info(
                "####  Running FSBased Full Backup  ####")
            db_helper = dbhelper.DbHelper(self.commcell)
            full_job = db_helper.run_backup(self.subclient, "FULL")

            before_full_backup_db_list = self.get_metadata()
            ##stopping postgres server before the restore
            self.postgres_helper_object.stop_postgres_server(pgsql_bin_dir, pgsql_data_dir)

            self.log.info(
                "####  Running Restore to disk Job  ####")
            path = ["2:{0}".format(full_job.job_id)]

            restore_job = self.backupset.restore_postgres_server(
                path,
                self.client.client_name,
                self.instance.instance_name,
                restore_to_disk=True,
                restore_to_disk_job=[int(full_job.job_id)],
                destination_path=restore_to_disk_path)
            self.log.info(
                "Started Restore to disk job with Job ID: %s", restore_job.job_id)
            if not restore_job.wait_for_completion():
                raise Exception(
                    "Failed to run restore to disk job with error: %s" % restore_job.delay_reason
                )
            self.log.info("## Successfully finished restore to disk job..##")

            data_directory_path = self.machine_object.join_path(
                restore_to_disk_path,
                restore_job.job_id,
                pgsql_data_dir.strip(separator).split(separator, 1)[1])
            pgsql_wal_directory = pgsql_wal_directory.rstrip(separator)
            log_directory_path = self.machine_object.join_path(
                restore_to_disk_path,
                restore_job.job_id,
                pgsql_wal_directory.strip(separator).split(separator, 1)[1])

            ##### move backup_label from wal dir to data dir
            self.log.info("Moving backup_label file to data directory")
            backup_label_path = self.machine_object.join_path(log_directory_path, 'backup_label')
            backup_label_path_data = self.machine_object.join_path(data_directory_path, 'backup_label')
            self.machine_object.move_file(backup_label_path, backup_label_path_data)

            ##### give permission to data directory and create recovery.conf inside data dir
            self.log.info("Creating recovery.conf file inside data directory")
            recovery_command = "restore_command = 'cp \"{0}\" \"%p\"'".format(
                self.machine_object.join_path(log_directory_path, "%f"))
            if "windows" in self.machine_object.os_info.lower():
                recovery_command = "restore_command = 'copy \"{0}\" \"%p\"'".format(
                    self.machine_object.join_path(log_directory_path, "%f"))
                recovery_command = recovery_command.replace("\\", "\\\\")
            self.machine_object.create_file(
                self.machine_object.join_path(data_directory_path, "recovery.conf"),
                recovery_command)

            self.log.info("Changing the permissions of restore directory.")
            command = "icacls {0} /t /grant Users\":(OI)(CI)F\"".format(restore_to_disk_path)
            if "unix" in self.machine_object.os_info.lower():
                command = "chown -R postgres:postgres {0}".format(restore_to_disk_path)
            output = self.machine_object.execute(command)
            if output.exception_message:
                raise Exception(output.exception_message)
            elif output.exception:
                raise Exception(output.exception)

            self.log.info("Starting the server using restored directories")
            self.postgres_helper_object.start_postgres_server(pgsql_bin_dir, data_directory_path)
            self.log.info("Sleeping for 2 mins before reconnection")
            time.sleep(120)

            self.pgsql_db_object.reconnect()
            after_restore_db_info = self.get_metadata()

            self.validate_data(before_full_backup_db_list, after_restore_db_info)

            self.log.info("Stopping the server.")
            self.postgres_helper_object.stop_postgres_server(pgsql_bin_dir, data_directory_path)
            self.log.info("Starting the server with original data directory")
            self.postgres_helper_object.start_postgres_server(pgsql_bin_dir, pgsql_data_dir)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
