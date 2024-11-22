# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  Initializes test case class object

    setup()                     --  Setup function for this testcase

    _run_restore()              --  Initiates the restore job for the specified subclient

    compression_valiadtion()    --  method to validate the usage of staging location
    and compression method on client

    tear_down()                 --  tear down function to delete automation generated data

    run()                       --  Main function for test case execution

"""
import time
import ast
from AutomationUtils import constants
from AutomationUtils import machine
from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.dbhelper import DbHelper

class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of PostgreSQL backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Compressed DumpBased backup/restore of PostgreSQL in Windows client"
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.tcinputs = {
            'TestDataSize': None
        }
        self.postgres_data_population_size = None
        self.dbhelper_object = None
        self.machine_object = None

    def setup(self):
        """setup function for this testcase"""

        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.postgres_db_password = self.postgres_helper_object.postgres_password
        self.dbhelper_object = DbHelper(self.commcell)
        self.machine_object = machine.Machine(self.client, self.commcell)
        if isinstance(self.tcinputs['TestDataSize'], str):
            self.tcinputs['TestDataSize'] = ast.literal_eval(self.tcinputs['TestDataSize'])

    def _run_restore(self, db_list):
        """Initiates the restore job for the specified subclient

        Args:

            db_list     (list)   -- List of databases to restore

        Returns:

            job                  -- returns JOB object

        Raises:

            Exception: if unable to start the restore job

        """
        job = self.subclient.restore_postgres_server(
            db_list, self.client.client_name, self.instance.instance_name)
        self.log.info(
            "Started %s Restore with Job ID: %s", self.backupset.backupset_name, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception("Failed to run restore job with error: %s" % (job.delay_reason))
        self.log.info("Successfully finished %s restore job", self.backupset.backupset_name)
        self.postgres_helper_object.refresh()
        return job

    def compression_valiadtion(self, log_directory, job_id, match_string):
        """method to validate the usage of staging location
        and compression method on client

        Args:

            log_directory   (str)   -- log directory of the client

            job_id          (str)   -- backup job id

            match_string    (str)   -- string that needs to be matched
            in the log file

        Raises:

            Exception: if compression or staging directory are not used

        """
        command = (
            "(Get-Content \"%s\" | "
            "Where-Object {$_ -match \"%s.*%s\"} | "
            "Foreach {$Matches[0]})") % (log_directory, job_id, match_string)
        output = self.machine_object.execute_command(command).formatted_output

        if output == '':
            raise Exception(
                "Exception in compression validation..!")

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "auto")
        ############## Deleting sPGStagingDir registry ##################
        self.log.info("Deleting sPGStagingDir registry Key")
        self.client.delete_additional_setting("PostGres", "sPGStagingDir")
        self.log.info("sPGStagingDir registry key is deleted Successfully")
        ############## Deleting sPGCompDump registry ####################
        self.log.info("Deleting sPGCompDump registry Key")
        self.client.delete_additional_setting("PostGres", "sPGCompDump")
        self.log.info("sPGCompDump registry key is deleted Successfully")

    def run(self):
        """Main function for test case execution"""

        try:
            self.postgres_data_population_size = self.tcinputs['TestDataSize']
            staging_directory = self.machine_object.join_path(self.client.install_directory, "Temp")
            self.log.info("Staging location Specified: %s", staging_directory)
            self.log.info("Postgres maintenance database:%s", self.instance.maintenance_database)
            ignoredb_list = [self.instance.maintenance_database, "template0"]
            pgsql_db_object = database_helper.PostgreSQL(
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_db_password,
                "postgres")
            self.log.info(
                "Postgres server Port: %s",
                self.instance.postgres_server_port_number)

            ################# Set ssPGCompDump registry key ########################
            self.log.info("Setting sPGCompDump registry Key")
            self.client.add_additional_setting("PostGres", "sPGCompDump", "STRING", "Y")
            self.log.info("sPGCompDump registry key is set Successfully")

            ################# Set sPGStagingDir registry key ########################
            self.log.info("Setting sPGStagingDir registry Key")
            self.client.add_additional_setting(
                "PostGres", "sPGStagingDir", "STRING", staging_directory)
            self.log.info("sPGStagingDir registry key is set Successfully")


            ################# DumpBased Backup/Restore Operations ########################
            self.log.info(
                "#" * (10) + "  DumpBased Backup/Restore Operations  " + "#" * (10))

            self.log.info("Generating Test Data")
            self.postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                self.postgres_data_population_size[0],
                self.postgres_data_population_size[1],
                self.postgres_data_population_size[2],
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_db_password,
                True,
                "auto_full_dmp")
            self.log.info("Test Data Generated successfully")

            db_list_before_backup = self.postgres_helper_object.get_subclient_database_list(
                self.subclient.subclient_name,
                self.backupset,
                pgsql_db_object.get_db_list())

            # Get the subclient content Info before backup
            self.log.info("Collect information of the subclient content before backup")
            for i in ignoredb_list:
                if i in db_list_before_backup:
                    db_list_before_backup.remove(i)

            self.log.info("Database list to backup:%s", db_list_before_backup)

            # Collecting Meta data
            before_full_backup_db_list = self.postgres_helper_object.generate_db_info(
                db_list_before_backup,
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_db_password)

            ###################### Running Full Backup ##############################
            self.log.info(
                "#" * (10) + "  Running Dumpbased Full Backup  " + "#" * (10))
            job = self.dbhelper_object.run_backup(self.subclient, "FULL")

            ############# validating Staging area and Compression dump backup ##########
            postgres_backup_log = self.postgres_helper_object.postgres_log_directory
            self.compression_valiadtion(
                postgres_backup_log,
                job.job_id,
                "sPGStagingDir reg key value.*[%s]" % (staging_directory))
            self.log.info("Staging location specified was used for storing the dump")
            self.compression_valiadtion(
                postgres_backup_log, job.job_id, "Command to run.*pg_dump.*-Fc")
            self.log.info("Data is backed-up using compression method.")
            self.log.info(
                "#######Validation of sPGStagingDir and sPGCompDump is PASSED..!!#######")

            # appending "/" to dbnames for dumpbased restore
            db_list = ["/" + database for database in db_list_before_backup]
            time.sleep(10)
            self.log.info("Sleeping for 10 seconds")

            self.log.info("Deleting Automation Created databases")
            self.postgres_helper_object.cleanup_tc_db(
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_db_password,
                "auto")


            # ###################### Running restore ###################################
            self.log.info("##### Running Dumpbased Restore  #####")
            self._run_restore(db_list)
            after_backup_db_list = self.postgres_helper_object.get_subclient_database_list(
                self.subclient.subclient_name,
                self.backupset,
                pgsql_db_object.get_db_list())
            if after_backup_db_list is None:
                raise Exception("Unable to get the database list")

            # Get subclient content info after restore
            self.log.info("Collect information of the subclient content after restore")
            for i in ignoredb_list:
                if i in after_backup_db_list:
                    after_backup_db_list.remove(i)
            after_restore_db_info = self.postgres_helper_object.generate_db_info(
                after_backup_db_list,
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_db_password)

            ########validation########
            self.log.info(
                "Validating the database information collected before Full Backup \
                 and after Inplace Restore for DumpBasedBackupset")
            # validate subclient content information collected before backup and after restore
            ret_code = self.postgres_helper_object.validate_db_info(
                before_full_backup_db_list, after_restore_db_info)
            if not ret_code:
                raise Exception("Data validation failure")
            self.log.info("Database information validation passed successfully")
            self.log.info("Testcase execution Completed..!!")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
