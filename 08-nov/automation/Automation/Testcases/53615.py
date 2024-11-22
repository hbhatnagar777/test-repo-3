# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  Setup function for the test case

    run()           --  run function of this test case

    run_backup_job()--  Method to run backup and check the completion status

    tear_down()     -- Tear down function for this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import machine
from Database.OracleUtils.oraclehelper import OracleHelper


class TestCase(CVTestCase):
    """Class for executing Oracle app free restore test case"""

    def __init__(self):
        """TestCase constructor"""
        super(TestCase, self).__init__()
        self.name = "Oracle app free restore test case"
        self.oracle_helper = None
        self.machine_object = None
        self.machine_object_root = None
        self.client_ip = None
        self.result_string = "Run of test case 53615 is incomplete"
        self.tcinputs = {
            "oracle_userpassword": None,
            "root_password": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.log.info(
            "%(boundary)s %(message)s %(boundary)s",
            {
                'boundary': "*" * 10,
                'message': "Initialize helper and SDK objects"
            }
        )
        self.machine_object = machine.Machine(self.client)
        self.client_ip = self.machine_object.ip_address
        self.oracle_helper = OracleHelper(self.commcell, self.client_ip, self.instance)
        self.oracle_helper.ora_machine_object = machine.Machine(machine_name=self.client_ip,
                                                                username=self.instance.os_user,
                                                                password=self.tcinputs['oracle_userpassword'])
        self.oracle_helper.base_directory = self.machine_object.join_path(self.client.install_directory,
                                                                          "Base")
        self.log.info('creation of oracle helper object succeeded.')
        self.log.info('CS set to %s', self.commcell)

    def run_backup_job(self, level):
        """Method to run backup and check the completion status

                    Args:
                        level           (str) -- The backup level that needs to be run
                                                  like FULL or INCREMENTAL

                    Returns:
                        object type  -   object of job class

                    Raises:
                        Exception:

                            If unable to run the backup job
                """
        # Perform a log switch
        self.oracle_helper.db_execute('alter system switch logfile')
        self.log.info("Logfile Switch before backup complete")
        # Run backup with the given level
        job_obj = self.subclient.backup(backup_level=level)
        if not job_obj.wait_for_completion():
            self.log.info(
                "Backup JOB ID: %s", job_obj.job_id)
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    level, job_obj.delay_reason))
        if job_obj.state in ("Completed w/ one or more errors", "Failed", "killed"):
            self.log.info(
                "Backup JOB ID: %s", job_obj.job_id)
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    level, job_obj.delay_reason))
        return job_obj

    def run(self):
        """Main function for test case execution"""

        try:
            cmd_output = ''
            # Connect to Oracle database and check if database is UP
            self.oracle_helper.db_connect(OracleHelper.CONN_SYSDBA)
            base_directory = self.machine_object.join_path(self.client.install_directory, "Base")
            cv_client_temp_path = self.machine_object.join_path(base_directory, "Temp")
            destination_path = self.machine_object.join_path(cv_client_temp_path,
                                                             "OracleTemp")
            database_status = self.oracle_helper.get_db_status()
            self.log.info('DB DBID: %s', self.instance.dbid)
            self.log.info('DB Status: %s', database_status)
            self.log.info('DB Version: %s', self.oracle_helper.ora_version)

            if database_status != 'READ WRITE':
                self.log.exception('Database status is invalid: %s', database_status)
                raise ValueError('Invalid database status: {0}'.format(database_status))
            # create table and populate with 10 records
            self.oracle_helper.db_create_table(
                'USERS', 'CV_TABLE_', 'SYS', 1)
            self.log.info('Successfully Created table and populated data')

            # Run a FULL backup
            self.log.info(
                "Running full backup on database: %s",
                self.instance.instance_name)
            full_job = self.run_backup_job('full')

            # run validation after full backup
            number_of_rows_created = self.oracle_helper.db_table_validate("SYS", "CV_TABLE_01")
            if number_of_rows_created != 10:
                self.log.info(" table validation after FULL backup failed ")
                raise Exception("Table validation failed after running FULL backup")

            # populating some more records into table and running incremental backup
            self.oracle_helper.db_populate_table('CV_TABLE_', 'SYS')

            self.log.info(
                "Running incremental backup on database: %s",
                self.instance.instance_name)
            inc_job = self.run_backup_job('incremental')

            # run validation after incremental backup

            number_of_rows_created = self.oracle_helper.db_table_validate("SYS", "CV_TABLE_01")
            if number_of_rows_created != 20:
                self.log.info(" table validation after INCREMENTAL backup failed ")
                raise Exception("Table validation failed after running INCREMENTAL backup")

            # Get the latest SCN until which database needs to be recovered
            self.log.info("Getting the SCN until which database needs to be recovered")

            recover_scn = self.oracle_helper.get_next_scn(inc_job.job_id)
            self.log.info("Got the recover SCN of incremental job as %s", recover_scn)

            backup_job_ids = [int(full_job.job_id), int(inc_job.job_id)]
            self.log.info("Starting app free restore with FULL and INCREMENTAL job")

            # Running the app free restore job
            restore_job = self.instance.restore_to_disk(self.client.client_name,
                                                        destination_path,
                                                        backup_job_ids,
                                                        self.instance.os_user,
                                                        self.tcinputs['oracle_userpassword'])
            if not restore_job.wait_for_completion():
                raise Exception(
                    "Failed to run app free restore job with error: {0}".format(
                        restore_job.delay_reason))
            self.log.info(
                " App free restore JOB ID: %s",
                restore_job.job_id)
            # The Following steps are to recover the database using backup pieces
            # that were restored using app free restore and validate the database"""
            # Create RMAN recover script with the staging path and SCN
            generated_script = self.oracle_helper.create_rman_restore_script(recover_scn,
                                                                             restore_job.job_id)

            # Copy the RMAN script to client and run the script to recover database
            # Stopping Commvault services to verify this feature for restore only clients too

            self.log.info("Stopping commvault services to verify"
                          " this feature for restore only clients too")
            self.client.stop_service()

            cmd_output = self.oracle_helper.execute_rman_restore_script(generated_script,
                                                                        "rman_script.rman")
            if str(cmd_output.output).find("ERROR") >= 0:
                self.log.error("RMAN script execution failed on the client")
                raise Exception("Failed to run RMAN script on the client after app free restore")
            else:
                self.log.info("RMAN script execution completed successfully on client")
                self.log.info("Database has been opened successfully after resetlogs")

                # Run validation after recovery if RMAN script was successfully executed
                number_of_rows_created = self.oracle_helper.db_table_validate("SYS", "CV_TABLE_01")
                if number_of_rows_created != 20:
                    self.log.info("table validation after INCREMENTAL backup failed ")
                    raise Exception("Table validation failed after INCREMENTAL backup")

                self.status = constants.PASSED
                self.result_string = "Run of test case 53615 is complete"
                self.log.info("Test Case Passed")

                # Start the Commvault services on the client which were stopped before recovery
                self.machine_object_root = machine.Machine(machine_name=self.client_ip,
                                                           username='root',
                                                           password=self.tcinputs['root_password'])
                instance_number = self.client.instance
                self.machine_object_root.execute_command("commvault -instance {0} start"
                                                         .format(instance_number))
                self.log.info("Starting Commvault services on client")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        self.log.info("Tear Down Function")
        self.log.info("Cleanup the tables created during test case run")
        # Drop the tables created during TC run
        self.oracle_helper.db_drop_table("SYS", "CV_TABLE_" + "01")
