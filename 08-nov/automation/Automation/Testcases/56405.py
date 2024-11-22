# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for # license information.
# --------------------------------------------------------------------------

"""
 Main file for executing this test case

 TestCase is the only class defined in this file.

 TestCase: Class for executing this test case

 TestCase:
     __init__()                  --  initialize TestCase class

     setup()                     --  setup method for test case

     validation_for_backup()     --  validate backup for logical dump

     validation_for_restore()    --  validate restore for logical dump

     wait_till_job_complete()    --  job will wait till complete

     run()                       --  run function of this test case

     tear_down()                 --  tears down the things created for running the testcase


 Input Example:

 "testCases": {
    "56405": {
        "ClientName" :"sp",
        "InstanceName" : "orc",
        "AgentName" : "Oracle",
        "BackupsetName" : "default",
        "javaPath":"",
        "dumpDir": "/sai/staging",
        "schemaValue" : [
        "REMOTE_SCHEDULER_AGENT",
        "SAI1",
        ]
        }
    }

 """
from time import sleep
from cvpysdk.subclient import Subclients
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import machine
from Database.OracleUtils.oraclehelper import OracleHelper


class TestCase(CVTestCase):
    """
    Test case class used to run a given test
    """

    def __init__(self):
        """TestCase constructor"""
        super(TestCase, self).__init__()
        self.name = (
            "Oracle Test Case 56405-'Oracle Logical Dump'"
            " testing for on permises subclient "
        )
        self.oracle_helper = None
        self.machine_object = None
        self.subclient_object = None
        self.storage_policy = None
        self.subclient_name_full = None
        self.subclient_name_schema = None
        self.registry_key = None
        self.registry_data = None
        self.domain_name = None
        self.user_name = None
        self.password = None
        self.tcinputs = {
            "javaPath": None,
            "dumpDir": None,
            "schemaValue": None
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
        self.oracle_helper = OracleHelper(self.commcell, self.client, self.instance)
        self.subclient_object = Subclients(self.instance)
        self.storage_policy = self.instance.subclients.get("default").storage_policy
        self.subclient_name_full = "{0}Full".format(self.id)
        self.subclient_name_schema = "{0}Schema".format(self.id)
        self.registry_key = "OracleAgent"
        self.registry_data = "sCV_JAVA_HOME"
        self.domain_name = (
            self.instance.properties.get("oracleInstance", {}).
            get("sqlConnect", {}).get("domainName", "")
        )
        self.user_name = self.oracle_helper.ora_sys_user
        self.password = self.oracle_helper.ora_sys_password
        self.log.info('CS set to %s', self.commcell)

    def validation_for_backup(self, job_id):
        """
        Method for validate Backup for logical dump
        Args:
             job_id (int) : Job id for Backup job
        Raise:
             validation of backup fail
        """
        self.log.info("validating backup started")
        default_job_path = self.machine_object.join_path("CV_JobResults", "2", "0")
        common_path = self.machine_object.join_path(default_job_path, job_id)
        remote_file_path = self.machine_object.join_path(self.client.job_results_directory,
                                                         common_path,
                                                         "RUN_DUMP.log")
        self.log.info("Log File Path to fetch RUN_DUMP Log : %s", remote_file_path)
        run_dump_log_content = self.machine_object.read_file(remote_file_path)
        if (run_dump_log_content.find('"CV_56405_USER"."CV_TABLE_01""."."CV_56405 with 10 rows dumped') > 0 and
                run_dump_log_content.find("Sending STATUS message SUCCESS") > 0):
            self.log.info("validating backup successful")
        else:
            raise Exception("validating backup failed")

    def validation_for_restore(self, job_id, expected_row_count):
        """
        Method for validate restore for logical dump
        Args:
             job_id             (int): Job id for restore job

             expected_row_count (int): row count before restore
        Raise:
             validation of restore fail
        """
        self.log.info("validating restore started")
        default_job_path = self.machine_object.join_path("CV_JobResults", "2", "0")
        common_path = self.machine_object.join_path(default_job_path, job_id)
        remote_file_path = self.machine_object.join_path(self.client.job_results_directory,
                                                         common_path,
                                                         "RUN_IMPORT.log ")
        self.log.info("Log File Path to fetch RUN_IMPORT Log : %s", remote_file_path)
        run_import_log_content = self.machine_object.read_file(remote_file_path)
        number_of_rows_created = (
            self.oracle_helper.
            db_table_validate("cv_56405_user", "CV_TABLE_01")
        )
        if (run_import_log_content.find('"CV_56405_USER"."CV_TABLE_01" exists') > 0 and
                run_import_log_content.find("Sending STATUS message SUCCESS") > 0 and
                number_of_rows_created == expected_row_count):
            self.log.info("validating restore successful")
        else:
            raise Exception("validating restore failed")

    def wait_till_job_complete(self, job, job_type):
        """
        Method for job wait till complete
        Args:
              job      (object):  object for job

              job_type  (str):     type of job
        """
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} job with error: {1}".format(
                    job.delay_reason, job_type))
        self.log.info("%s completed successful JOB ID: %s", job_type, job.job_id)
        self.log.info("sleeping for 5 second after successfully %s", job_type)
        sleep(5)

    def run(self):
        """ Main function for test case execution """
        try:
            # Adding Registry key on client
            self.log.info("Setting the registry key on the client for JAVA path")
            self.machine_object.create_registry(self.registry_key,
                                                self.registry_data,
                                                self.tcinputs["javaPath"])
            # creating subclient for database mode
            self.log.info(
                "creating logical subclient with export mode Full Database, "
                "staging path and override instance credentials."
            )
            self.subclient_object.add_oracle_logical_dump_subclient(
                self.subclient_name_full,
                self.storage_policy,
                self.tcinputs["dumpDir"],
                self.user_name,
                self.domain_name,
                self.password,
                True)
            self.instance.refresh()
            self.log.info("subclient created successful")
            self.log.info("Creating oracle user, table and populating data before backup")
            # Connect to source Oracle database and check if database is UP/OPEN
            self.oracle_helper.db_connect(OracleHelper.CONN_SYSDBA)
            self.log.info("connected to source database")
            source_database_status = self.oracle_helper.get_db_status()
            self.log.info('DB DBID: %s', self.instance.dbid)
            self.log.info('DB Status: %s', source_database_status)
            self.log.info('DB Version: %s', self.oracle_helper.ora_version)

            if source_database_status != 'READ WRITE':
                self.log.exception('Database status is invalid: %s', source_database_status)
                raise ValueError('Invalid status for source database: {0}'.format
                                 (source_database_status))
            ts_name = 'CV_56405'
            user = 'cv_56405_user'
            table_prefix = "CV_TABLE_"
            table_limit = 1
            num_of_files = 1
            data_file_location = self.oracle_helper.db_fetch_dbf_location()
            # create a sample tablespace
            self.oracle_helper.db_create_tablespace(ts_name, data_file_location, num_of_files)

            # create user and table and populate with 10 records
            self.log.info("Creating users on source")
            self.oracle_helper.db_create_user(user, ts_name)
            self.oracle_helper.db_create_table(ts_name, table_prefix, user, table_limit)
            self.log.info('Successfully Created table and populated data')
            # Backup for database mode
            self.log.info("Backing Up For Database Mode")
            subclient_obj = self.instance.subclients.get(self.subclient_name_full)

            job = subclient_obj.backup("full")
            self.wait_till_job_complete(job, "FULL backup")
            # Backup validation for database mode
            self.validation_for_backup(job.job_id)
            # restore for database mode
            self.log.info("restoring for full database mode")

            job1 = subclient_obj.restore_in_place(db_password=self.password,
                                                  database_list=["/"],
                                                  destination_path=self.tcinputs["dumpDir"])
            self.wait_till_job_complete(job1, "restoring for full database mode")
            # restore validation for database mode
            self.validation_for_restore(job1.job_id, 10)
            # Adding known schema for subclient
            self.tcinputs["schemaValue"].append('cv_56405_user')
            # creating subclient for schema mode
            self.log.info(
                "creating logical subclient with export mode Schema, "
                "staging path and override instance credentials."
            )
            self.subclient_object.add_oracle_logical_dump_subclient(
                self.subclient_name_schema,
                self.storage_policy,
                self.tcinputs["dumpDir"],
                self.user_name,
                self.domain_name,
                self.password,
                False,
                schema_value=self.tcinputs["schemaValue"])
            self.instance.refresh()
            self.log.info("subclient created successful")
            # Backup for schema mode
            self.log.info("Backing Up For Schema Mode")
            subclient_obj = self.instance.subclients.get(self.subclient_name_schema)
            job = subclient_obj.backup("full")
            self.wait_till_job_complete(job, "FULL backup")
            # Backup validation for schema mode
            self.validation_for_backup(job.job_id)
            # restore for schema mode
            self.log.info("restoring for Schema mode")
            job1 = subclient_obj.restore_in_place(db_password=self.password,
                                                  database_list=["/"],
                                                  destination_path=self.tcinputs["dumpDir"])
            self.wait_till_job_complete(job1, "restoring for Schema mode")
            # restore validation for schema mode
            self.validation_for_restore(job1.job_id, 10)
        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED

    def tear_down(self):
        self.log.info("Tear Down Function")
        self.log.info("Cleanup the subclient created during test case run")
        # Drop the subclient created during TC run
        try:
            self.subclient_object.delete(self.subclient_name_full)
            self.subclient_object.delete(self.subclient_name_schema)
        except Exception as exp:
            self.log.error("Clean up failed")

